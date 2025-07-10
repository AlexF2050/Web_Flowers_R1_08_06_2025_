from rest_framework.exceptions import APIException

class SkipError(APIException):
    status_code = 400
    default_detail = 'Операция была пропущена'
    default_code = 'skip_error'