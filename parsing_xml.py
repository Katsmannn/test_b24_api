import urllib
import datetime as dt
import time
import xml.dom.minidom as minidom

from fast_bitrix24 import Bitrix

from setting import MY_WEBHOOK


TIME_FOR_UPDATE_VALUTES = 8  # Time for update currency: 08:XX
# Code currency for update
CURRENCY_NAMES = [
    'EUR',
    'USD',
    'KZT',
    'PLN',
]
WEBHOOK = MY_WEBHOOK  # Webhook bitrix24


def xml_parse():
    '''Get currency values from cbr.ru (parse XML).'''
    currency_values = dict()
    now = dt.datetime.now().strftime('%d/%m/%Y')
    url = f'https://cbr.ru/scripts/XML_daily.asp?date_req={now}'
    xml = urllib.request.urlopen(url)
    doc = minidom.parse(xml)
    vals = doc.getElementsByTagName("Valute")
    for element in vals:
        name = element.getElementsByTagName("CharCode")[0].childNodes[0].data
        if name in CURRENCY_NAMES:
            value = element.getElementsByTagName("Value")[0].childNodes[0].data
            currency_values[name] = value
    return currency_values


def update_valute_to_bitrix(name_cur, value):
    '''Update currency on Bitrix24.'''
    b = Bitrix(WEBHOOK)
    task = [
        {
            'ID': name_cur,
            'fields': {
                'AMOUNT': float(value.replace(',', '.'))
            }
        }
    ]
    b.call(
        'crm.currency.update',
        task)


def add_valute_to_bitrix(name_cur, value):
    '''Add currency on Bitrix24.'''
    b = Bitrix(WEBHOOK)
    task = [
        {
            'fields': {
                'CURRENCY': name_cur,
                'AMOUNT_CNT': 1,
                'AMOUNT': float(value.replace(',', '.'))
            }
        }
    ]
    b.call(
        'crm.currency.add',
        task)


def get_valute_list_from_bitrix():
    '''Get currency list from Bitrix24.'''
    b = Bitrix(WEBHOOK)
    valute_from_bitrix = b.get_all(
        'crm.currency.list',
    )
    return [valute['CURRENCY'] for valute in valute_from_bitrix]


def main():
    while True:
        if dt.datetime.now().hour == TIME_FOR_UPDATE_VALUTES:
            list_valute_to_update = xml_parse()
            list_valute_from_bitrix = get_valute_list_from_bitrix()
            for valute, value in list_valute_to_update.items():
                if valute in list_valute_from_bitrix:
                    update_valute_to_bitrix(valute, value)
                else:
                    add_valute_to_bitrix(valute, value)
        time.sleep(3599)


if __name__ == '__main__':
    main()
