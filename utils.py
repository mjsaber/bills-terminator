import re

def extract_phone_number(raw_input):
    reg = re.compile("\d{3}-\d{3}-\d{4}")
    return reg.findall(raw_input.strip())[0]


def is_fee(raw_input):
    reg = re.compile("[$]\d+.\d{2}")
    return reg.match(raw_input.strip()) is not None


def extract_fee(raw_input):
    reg = re.compile("[$]\d+.\d{2}")
    fee_string = reg.findall(raw_input.strip())[0]
    return float(fee_string[1:])


def alter_phone_format(phone):
    '''
    Alter phone number format from xxx-xxx-xxxx to +1xxxxxxxxxx
    '''
    return '+1' + phone.replace('-', '')


if __name__ == '__main__':
    assert is_fee('$1.00')
