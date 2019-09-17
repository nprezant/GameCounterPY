
class Error(Exception):
    '''Base class for exceptions in this module.'''
    pass

class MoveGridItemFocusError(Error):
    '''Exception raised for errors moving focus.

    Attributes:
        row -- current grid item row
        column -- current grid item column
        nextRow -- requested next grid item row
        nextColumn -- requested next grid item column
        message -- explanation of the error
    '''

    def __init__(self, row, column, nextRow, nextColumn, message):
        self.row = row
        self.column = column
        self.nextRow = nextRow
        self.nextColumn = nextColumn
        self.message = message


class MoveGridFocusError(Error):
    '''Exception raised for errors moving focus between image grids.

    Attributes:
        index -- current grid index
        nextIndex -- requested next grid index
        message -- explanation of the error
    '''

    def __init__(self, index, nextIndex, message):
        self.index = index
        self.nextIndex = nextIndex
        self.message = message
