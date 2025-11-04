from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
