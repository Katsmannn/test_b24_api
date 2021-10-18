import requests
import datetime as dt

from fast_bitrix24 import Bitrix

from setting import TEST_SERVER_URL, MY_WEBHOOK


WEBHOOK = MY_WEBHOOK
URL = TEST_SERVER_URL


class DataError(Exception):
    pass


def get_client_from_bitrix(bitrix, phone):
    '''Get client's id from Bitrix24 by phone number.'''
    params = {
        'select': ['ID', 'PHONE']
    }
    clients_from_bitrix = bitrix.get_all(
        'crm.contact.list',
        params
    )
    client_id = [
        x.get('ID') for x in clients_from_bitrix
        if x.get('PHONE') is not None
        and x.get('PHONE')[0].get('VALUE') == phone
    ]
    return client_id[0] if client_id != [] else None


def add_client_to_bitrix(bitrix, client):
    '''Create client on Bitrix24.'''
    task = [
        {
            'fields': {
                'NAME': client['name'],
                'LAST_NAME': client['surname'],
                'PHONE': [{'VALUE': client['phone'], 'VALUE_TYPE': 'WORK'}],
                'ADDRESS': client['adress'],
            },
            'params': {'REGISTER_SONET_EVENT': 'Y'}
        }
    ]
    bitrix.call(
        'crm.contact.add',
        task
    )


def get_deal_in_bitrix(bitrix, deal):
    '''Get deal from Bitrix24.'''
    params = {
            'filter': {'UF_CRM_DELIVERY_CODE': deal['delivery_code']},
            'select': [
                'ID',
                'UF_CRM_DELIVERY_ADDRESS',
                'CLOSEDATE',
                'CONTACT_ID',
            ],
    }
    deal_list = bitrix.get_all(
        'crm.deal.list',
        params,
    )
    return deal_list[0] if deal_list != [] else None


def get_products_from_bitrix(bitrix, id):
    '''Get products by deal's id from Bitrix24.'''
    if id is None:
        return None
    params = {
        'ID': id
    }
    products = bitrix.get_all(
        'crm.deal.productrows.get',
        params
    )
    return [x['PRODUCT_NAME'] for x in products]


def update_products_in_bitrix(bitrix, id, data):
    '''Update list of products for deal by id.'''
    params = [{
        'ID': id,
        'rows': [
            {'PRODUCT_NAME': product} for product in data
        ]
    }]
    bitrix.call(
        'crm.deal.productrows.set',
        params
    )


def add_deal_in_bitrix(bitrix, id_client, deal):
    '''Create deal in Bitrix24.'''
    params = {
        'fields': {
            'TITLE': deal['title'],
            'COMMENTS': deal['description'],
            'CONTACT_ID': id_client,
            'UF_CRM_DELIVERY_ADDRESS': deal['delivery_adress'],
            'CLOSEDATE': dt.datetime.strptime(
                deal['delivery_date'], '%Y-%m-%d:%H:%M'
            ),
            'UF_CRM_DELIVERY_CODE': deal['delivery_code'],
        },
        'params': {'REGISTER_SONET_EVENT': 'Y'}
    }
    bitrix.call(
        'crm.deal.add',
        params
    )


def update_deal_in_bitrix(bitrix, id_deal, param):
    '''Update one field of deal in Bitrix24.'''
    params = {
        'id': id_deal,
        'fields': param,
        'params': {'REGISTER_SONET_EVENT': 'Y'}
    }
    bitrix.call(
        'crm.deal.update',
        params
    )


def check_data(deal):
    '''Check data on query.'''
    title = deal.get('title')
    description = deal.get('description')
    client = deal.get('client')
    products = deal.get('products')
    delivery_adress = deal.get('delivery_adress')
    delivery_date = deal.get('delivery_date')
    delivery_code = deal.get('delivery_code')
    if (
        (title is None)
        or (description is None)
        or (client is None)
        or (products is None)
        or (delivery_adress is None)
        or (delivery_date is None)
        or (delivery_code is None)
    ):
        return False
    if not (
        (isinstance(title, str))
        or (isinstance(description, str))
        or (isinstance(client, dict))
        or (isinstance(products, list))
        or (isinstance(delivery_adress, str))
        or (isinstance(delivery_date, str))
        or (isinstance(delivery_code, str))
    ):
        return False
    return True


def handle_deal(deal):
    if not check_data(deal):
        raise DataError
    my_bitrix = Bitrix(WEBHOOK)
    client = deal.pop('client')
    id_client_b24 = get_client_from_bitrix(my_bitrix, client['phone'])
    if id_client_b24 is None:
        add_client_to_bitrix(my_bitrix, client)
        id_client_b24 = get_client_from_bitrix(my_bitrix, client['phone'])
    bitrix_deal = get_deal_in_bitrix(my_bitrix, deal)
    if bitrix_deal is None:
        add_deal_in_bitrix(my_bitrix, id_client_b24, deal)
        bitrix_deal = get_deal_in_bitrix(my_bitrix, deal)
    if bitrix_deal['CONTACT_ID'] is None:
        update_deal_in_bitrix(
            my_bitrix,
            bitrix_deal['ID'],
            {'CONTACT_ID': id_client_b24}
        )
    if deal['delivery_adress'] != bitrix_deal['UF_CRM_DELIVERY_ADDRESS']:
        update_deal_in_bitrix(
            my_bitrix,
            bitrix_deal['ID'],
            {'UF_CRM_DELIVERY_ADDRESS': deal['delivery_adress']}
        )
    new_delivery_date = dt.datetime.strptime(
        deal['delivery_date'], '%Y-%m-%d:%H:%M'
    )
    if new_delivery_date.isoformat()[:10] != bitrix_deal['CLOSEDATE'][:10]:
        update_deal_in_bitrix(
            my_bitrix,
            bitrix_deal['ID'],
            {'CLOSEDATE': new_delivery_date}
        )
    products_from_bitrix = get_products_from_bitrix(
        my_bitrix,
        bitrix_deal['ID']
    )
    products = deal['products']
    products.extend(products_from_bitrix)
    if set(products) != set(products_from_bitrix):
        update_products_in_bitrix(my_bitrix, bitrix_deal['ID'], set(products))


def main():
    try:
        response = requests.get(URL)
        handle_deal(response.json())
    except DataError:
        print('Data error')
    except Exception:
        pass


if __name__ == '__main__':
    main()
