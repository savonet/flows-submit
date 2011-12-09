from sqlalchemy.types import Text, TypeDecorator, CHAR
from sqlalchemy.schema import CheckConstraint

# Simple type for tokens

class Token(TypeDecorator):
  impl = CHAR
  
  def load_dialect_impl(self, dialect):
    return dialect.type_descriptor(CHAR(40))

class NonEmptyConstraint(CheckConstraint):
  def __init__(self, col):
    CheckConstraint.__init__(self, "length(" + str(col) + ") > 0")
