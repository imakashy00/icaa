import enum
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- Enums ---
class RuleType(enum.Enum):
    EXCLUSION = "exclusion"
    WAITING_PERIOD = "waiting_period"
    SUB_LIMIT = "sub_limit"


class ClaimStatus(enum.Enum):
    INITIATED = "initiated"
    UNDER_REVIEW = "under_review"
    PARTIALLY_APPROVED = "partially_approved"
    APPROVED = "approved"
    REJECTED = "rejected"


class HospitalType(enum.Enum):
    NETWORK = "network"
    NON_NETWORK = "non_network"


# --- Global Reference Tables ---
class ICDMaster(Base):
    __tablename__ = "icd_master"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    icd_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    rule_exclusions: Mapped[List["PolicyRuleExclusion"]] = relationship(
        back_populates="icd_reference"
    )
    medical_details: Mapped[List["ClaimMedicalDetail"]] = relationship(
        back_populates="icd_reference"
    )

class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id = mapped_column(Uuid, primary_key=True)
    claim_id = mapped_column(ForeignKey("claims.id"))

    filename = mapped_column(String(255))
    document_type = mapped_column(String(100))
    storage_path = mapped_column(Text)

    uploaded_at = mapped_column(DateTime)


# --- Policy Domain Tables ---
class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    policy_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    tpa_id: Mapped[str] = mapped_column(String(50))
    policy_holder_name: Mapped[str] = mapped_column(String(255))
    address = mapped_column(Text)
    city = mapped_column(String(100))
    state = mapped_column(String(100))
    pin_code = mapped_column(String(20))
    email = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    commencement_date: Mapped[date] = mapped_column(Date)

    # Using Numeric for high-precision financial tracking
    total_sum_insured: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    available_sum_insured: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    room_rent_cap_per_day: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    co_pay_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)

    # Relationships
    beneficiaries: Mapped[List["PolicyBeneficiary"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    rules_exclusions: Mapped[List["PolicyRuleExclusion"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    claims: Mapped[List["Claim"]] = relationship(back_populates="policy")


class PolicyBeneficiary(Base):
    __tablename__ = "policy_beneficiaries"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("policies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    beneficiary_relationship: Mapped[str] = mapped_column(
        String(50)
    )  # Self, Spouse, Child
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    policy: Mapped["Policy"] = relationship(back_populates="beneficiaries")


class PolicyRuleExclusion(Base):
    __tablename__ = "policy_rules_exclusions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("policies.id"), index=True)
    icd_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("icd_master.id"), nullable=True
    )
    condition_name: Mapped[str] = mapped_column(String(255))
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType))
    waiting_period_months: Mapped[int] = mapped_column(default=0)
    max_payout_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Relationships
    policy: Mapped["Policy"] = relationship(back_populates="rules_exclusions")
    icd_reference: Mapped[Optional["ICDMaster"]] = relationship(
        back_populates="rule_exclusions"
    )


# --- Claims Lifecycle Tables ---
class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    beneficiary_id = mapped_column(ForeignKey("policy_beneficiaries.id"))
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("policies.id"), index=True)
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus), default=ClaimStatus.INITIATED
    )
    fraud_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)
    current_agent_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    next_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Auditing timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    policy: Mapped["Policy"] = relationship(back_populates="claims")
    medical_details: Mapped[List["ClaimMedicalDetail"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    financials: Mapped["ClaimFinancial"] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    hospital_code: Mapped[str] = mapped_column(String(50), unique=True)
    hospital_name: Mapped[str] = mapped_column(String(255))
    hospital_type: Mapped[HospitalType] = mapped_column(Enum(HospitalType))
    address: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean)


class ClaimMedicalDetail(Base):
    __tablename__ = "claim_medical_details"

    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claims.id"), primary_key=True)
    hospital_name: Mapped[str] = mapped_column(String(255))
    hospital_type: Mapped[HospitalType] = mapped_column(Enum(HospitalType))
    admission_date: Mapped[date] = mapped_column(Date)
    discharge_date: Mapped[date] = mapped_column(Date)
    icd_id: Mapped[UUID] = mapped_column(ForeignKey("icd_master.id"), index=True)
    procedure_name: Mapped[str] = mapped_column(String(255))
    room_category_used: Mapped[str] = mapped_column(String(100))

    # Relationships
    claim: Mapped["Claim"] = relationship(back_populates="medical_details")
    icd_reference: Mapped["ICDMaster"] = relationship(back_populates="medical_details")
    hospital_id = ForeignKey("hospitals.id")

class ClaimFinancial(Base):
    __tablename__ = "claim_financials"

    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claims.id"), primary_key=True)

    # Extracted requested amounts
    requested_hospitalization: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    requested_pre_hospitalization: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    requested_post_hospitalization: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    requested_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0)

    # Calculated adjudicated amounts
    approved_hospitalization: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0)
    approved_pre_hospitalization: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    approved_post_hospitalization: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    final_approved_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0)

    deduction_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Audits partial payment choices

    # Relationships
    claim: Mapped["Claim"] = relationship(back_populates="financials")
