from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import relationship

from db.database import Base

Base.metadata.schema = "seatbook"


class User(Base):
    __table_args__ = {"schema": "seatbook"}
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    tg_id = Column(BigInteger, unique=True)
    chat_id = Column(BigInteger, unique=True)
    full_name = Column(String, unique=True, nullable=False)


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # type должен быть одним из допустимых значений
        CheckConstraint(
            "type IN ('personal', 'guest', 'personal_candidate', 'guest_candidate')",
            name="ck_booking_type_valid",
        ),
        # если type = guest | guest_candidate → guest_full_name обязателен
        CheckConstraint(
            "(type NOT IN ('guest', 'guest_candidate')) OR guest_full_name IS NOT NULL",
            name="ck_guest_full_name_required",
        ),
        # если type = *_candidate → seat_number = NULL, иначе seat_number NOT NULL
        CheckConstraint(
            "((type IN ('personal_candidate', 'guest_candidate')) AND seat_number IS NULL) "
            "OR ((type IN ('personal', 'guest')) AND seat_number IS NOT NULL)",
            name="ck_seat_number_consistency",
        ),
        Index(
            "uq_booking_date_seat",
            "booking_date",
            "seat_number",
            unique=True,
            postgresql_where=text("seat_number IS NOT NULL"),
        ),
        {"schema": "seatbook"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("seatbook.users.id", ondelete="CASCADE"), nullable=False
    )
    booking_date = Column(Date, nullable=False)
    seat_number = Column(String, nullable=True)
    type = Column(String, nullable=False)
    guest_full_name = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", backref="bookings")
