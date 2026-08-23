import sys

def error_msg_info(error, error_detail:sys):
    exc_tb = error_detail.exc_info()
    file_name = exc_tb.tb_frame.f_code.co_filename  #extract file name from exception info
    line_no = exc_tb.tb_lineno  #extract the line no. in the file where the exception occurred
    
    error_msg = "Error has ocurred in the python script: Name = [{0}], Line Number = [{1}], Error Message = [{2}]".format(
        file_name, line_no, str(error)
    )

    return error_msg

class CustomException(Exception):
    def __init__(self, error_msg, error_detail:sys):
        super.__init__(error_msg)
        self.error_msg = error_msg_info(error_msg, error_detail=error_detail)

    def __str__(self):
        return self.error_msg


