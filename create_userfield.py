from fast_bitrix24 import Bitrix

from setting import TEST_SERVER_URL, MY_WEBHOOK


WEBHOOK = MY_WEBHOOK
URL = TEST_SERVER_URL
BITRIX_USERFIELDS = [
    'DELIVERY_CODE',
    'DELIVERY_ADDRESS',
]


def check_userfield_is_exist(bitrix, userfield_name):
    deal_fields = bitrix.get_all(
        'crm.deal.fields'
    )
    return deal_fields.get(userfield_name)


def add_userfield_on_bitrix(bitrix, userfield_name):
    if check_userfield_is_exist(userfield_name) is None:
        params = {
            'fields': {
                'FIELD_NAME': userfield_name,
                'USER_TYPE_ID': 'string'
            }
        }
        bitrix.call(
            'crm.deal.userfield.add',
            params
        )


def main():
    my_bitrix = Bitrix(WEBHOOK)
    for userfield in BITRIX_USERFIELDS:
        bitrix_userfield = f'UF_CRM_{userfield}'
        add_userfield_on_bitrix(my_bitrix, bitrix_userfield)


if __name__ == '__main__':
    main()
