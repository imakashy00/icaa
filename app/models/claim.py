import enum
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SectionType(str, enum.Enum):
    DEFINITION = "definition"
    EXCLUSION = "exclusion"
    INCLUSION = "inclusion"
    WAITING_PERIOD = "waiting_period"
    SUB_LIMIT = "sub_limit"
    COPAY = "copay"
    CONDITION = "condition"
    CLAIM_PROCEDURE = "claim_procedure"
    GENERAL = "general"


# --- Enums ---

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

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    icd_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    medical_details: Mapped[List["ClaimMedicalDetail"]] = relationship(
        back_populates="icd_reference"
    )


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id"),
        nullable=False,
        index=True,
    )

    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    claim: Mapped["Claim"] = relationship(back_populates="documents")


class Company(Base):
    """One row per insurer. Policies belong to a company."""

    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationship configuration
    policy_documents: Mapped[List["PolicyDocument"]] = relationship(
        back_populates="company"
    )


class PolicyDocument(Base):
    """
    One row per policy document (a company can have many policies,
    and multiple versions of the same policy over time via `version`).
    """

    __tablename__ = "policy_documents"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "policy_code", "version", name="uq_policy_identity"
        ),
    )

    # Core Columns
    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_code: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(50), default="v1")

    # Date Columns
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit trail
    source_file: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # S3 or local path to the original PDF

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company", back_populates="policy_documents"
    )

    clauses: Mapped[List["PolicyClause"]] = relationship(
        "PolicyClause", back_populates="policy_document", cascade="all, delete-orphan"
    )

    coverage: Mapped[Optional["PolicyCoverage"]] = relationship(
        "PolicyCoverage",
        back_populates="policy",
        cascade="all, delete-orphan",
    )


class PolicyClause(Base):
    """
    One row per clause-level chunk of a policy document. This is what gets
    vector-searched at audit time, always filtered by `policy_id` so a
    query for one claim never touches another company's (or even another
    policy's) clauses.
    """

    __tablename__ = "policy_clauses"

    # Core Columns
    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    # Note: Updated ForeignKey target from "policies.id" to "policy_docs.id"
    policy_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("policy_documents.id"), nullable=False, index=True
    )

    # Content Columns
    clause_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    heading: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_type: Mapped[SectionType] = mapped_column(
        Enum(SectionType), nullable=False, default=SectionType.GENERAL, index=True
    )
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Vector Embedding
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536), nullable=True)

    # Relationships
    policy_document: Mapped["PolicyDocument"] = relationship(
        "PolicyDocument", back_populates="clauses"
    )


class PolicyCoverage(Base):
    """
    One row per policy: the normalized, deterministic-audit-ready fields
    extracted once by the LLM at ingestion time. `raw_extraction` stores the
    full extraction output for traceability / re-review without re-calling
    the LLM.
    """

    __tablename__ = "policy_coverages"

    # Core Columns
    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    # Note: Updated ForeignKey target from "policies.id" to "policy_docs.id"
    policy_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("policy_documents.id"), nullable=False, unique=True, index=True
    )

    # Extracted Metrics
    sum_insured: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True
    )

    # JSON-backed Fields (Typed as Optional[Union[Dict, List]] for versatility)
    room_rent_limit: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # {"type": "percentage_of_si", "value": 1}
    copay: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )  # [{"condition": "...", "percentage": 10}]
    waiting_periods: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # {"initial_days": 30, "pre_existing_disease_months": 36, ...}
    sub_limits: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )  # [{"procedure_or_category": "cataract", "limit_type": "fixed_amount", "value": 25000}]
    permanent_exclusions: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )  # ["...", "..."]

    # Audit trail
    raw_extraction: Mapped[Optional[Union[Dict[str, Any], List[Any]]]] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    policy: Mapped["PolicyDocument"] = relationship(
        "PolicyDocument", back_populates="coverage"
    )


# --- Policy Domain Tables ---
class PolicyContract(Base):
    __tablename__ = "policy_contracts"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    policy_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id"),
        index=True,
    )
    policy_document_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("policy_documents.id"), index=True, nullable=True
    )
    tpa_id: Mapped[str] = mapped_column(String(50))
    policy_holder_name: Mapped[str] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    commencement_date: Mapped[date] = mapped_column(Date)

    # Using Numeric for high-precision financial tracking
    total_sum_insured: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    available_sum_insured: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Relationships
    members: Mapped[List["PolicyMember"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    claims: Mapped[List["Claim"]] = relationship(back_populates="policy")
    policy_document: Mapped["PolicyDocument"] = relationship()

class PolicyMember(Base):
    __tablename__ = "policy_members"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("policy_contracts.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    relationship_to_holder: Mapped[str] = mapped_column(
        String(50)
    )  # Self, Spouse, Child
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    policy: Mapped["PolicyContract"] = relationship(back_populates="members")
    claims: Mapped[List["Claim"]] = relationship(back_populates="member")

# --- Claims Lifecycle Tables ---
class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    member_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("policy_members.id"), index=True, nullable=True
    )
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("policy_contracts.id"), index=True
    )
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
    policy: Mapped["PolicyContract"] = relationship(back_populates="claims")
    medical_details: Mapped[List["ClaimMedicalDetail"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    financial: Mapped["ClaimFinancial"] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    documents: Mapped[List["ClaimDocument"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    member: Mapped[Optional["PolicyMember"]] = relationship(back_populates="claims")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    hospital_code: Mapped[str] = mapped_column(String(50), unique=True)
    hospital_name: Mapped[str] = mapped_column(String(255))
    hospital_type: Mapped[HospitalType] = mapped_column(Enum(HospitalType))
    address: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean)


class ClaimMedicalDetail(Base):
    __tablename__ = "claim_medical_details"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id"), nullable=False, index=True
    )
    admission_date: Mapped[date] = mapped_column(Date)
    discharge_date: Mapped[date] = mapped_column(Date)
    icd_id: Mapped[UUID] = mapped_column(ForeignKey("icd_master.id"), index=True)
    procedure_name: Mapped[str] = mapped_column(String(255))
    room_category_used: Mapped[str] = mapped_column(String(100))
    hospital_id: Mapped[UUID] = mapped_column(
        ForeignKey("hospitals.id"), nullable=False, index=True
    )
    # Relationships
    claim: Mapped["Claim"] = relationship(back_populates="medical_details")
    icd_reference: Mapped["ICDMaster"] = relationship(back_populates="medical_details")
    hospital: Mapped["Hospital"] = relationship()


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
    approved_hospitalization: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.0
    )
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
    claim: Mapped["Claim"] = relationship(back_populates="financial")
