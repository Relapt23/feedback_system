from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FeedbackInfo(Base):
    __tablename__ = "feedback_info"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]
    status: Mapped[str]
    timestamp: Mapped[int]
    sentiment: Mapped[str]
    category: Mapped[str]
