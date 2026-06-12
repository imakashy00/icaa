import random
from datetime import timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your database components
from app.core.settings import settings
from app.models.claim import Base  # Ensure this imports your SQLAlchemy Base with all tables

# Import your specific models so Base knows they exist
from app.models.claim import (
    ICDMaster,
    Policy,
    PolicyBeneficiary,
    PolicyRuleExclusion,
    Claim,
    ClaimMedicalDetail,
    ClaimFinancial,
    RuleType,
    ClaimStatus,
    HospitalType,
)

# Initialize Faker
fake = Faker()

# 1. Use your production engine configuration
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def seed_database():
    session = SessionLocal()
    try:
        print("Connecting to PostgreSQL database...")

        # DANGER: Dropping all tables completely.
        # Only run this in a designated local/dev testing container environment!
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print("Database schema dropped and re-applied cleanly.")

        # 2. Seed ICD Master Reference Tables
        icd_pool = [
            ICDMaster(
                icd_code="I21.9",
                description="Acute myocardial infarction, unspecified (Heart Attack)",
                is_chronic=False,
            ),
            ICDMaster(
                icd_code="E11.9",
                description="Type 2 diabetes mellitus without complications",
                is_chronic=True,
            ),
            ICDMaster(
                icd_code="J45.909",
                description="Unspecified asthma, uncomplicated",
                is_chronic=True,
            ),
            ICDMaster(
                icd_code="M17.9",
                description="Osteoarthritis of knee, unspecified",
                is_chronic=False,
            ),
            ICDMaster(
                icd_code="K59.00",
                description="Constipation, unspecified",
                is_chronic=False,
            ),
        ]
        session.add_all(icd_pool)
        session.flush()  # Pushes records to Postgres to acquire generated UUIDs
        print(f"Successfully loaded {len(icd_pool)} baseline ICD records.")

        # 3. Main Entity Seeding Loop
        for i in range(10):
            start_dt = fake.date_between(start_date="-2y", end_date="-1y")
            end_dt = start_dt + timedelta(days=365)

            policy = Policy(
                policy_no=f"POL-{fake.unique.random_number(digits=8)}",
                tpa_id=f"TPA-{random.randint(10, 99)}",
                policy_holder_name=fake.name(),
                active=True,
                start_date=start_dt,
                end_date=end_dt,
                commencement_date=start_dt,
                total_sum_insured=Decimal("500000.00"),
                available_sum_insured=Decimal("500000.00"),
                room_rent_cap_per_day=Decimal("5000.00"),
                co_pay_percentage=Decimal("10.00"),
            )
            session.add(policy)
            session.flush()  # Essential for Postgres to assign policy.id primary key

            # Add Primary & Dependent Beneficiaries
            holder = PolicyBeneficiary(
                policy_id=policy.id,
                name=policy.policy_holder_name,
                beneficiary_relationship="Self",
                gender=random.choice(["Male", "Female"]),
                date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=60),
            )
            dependent = PolicyBeneficiary(
                policy_id=policy.id,
                name=fake.name(),
                beneficiary_relationship=random.choice(["Spouse", "Child"]),
                gender=random.choice(["Male", "Female"]),
                date_of_birth=fake.date_of_birth(minimum_age=1, maximum_age=24),
            )
            session.add_all([holder, dependent])

            # Assign a specific policy restriction rule
            chosen_icd = random.choice(icd_pool)
            rule = PolicyRuleExclusion(
                policy_id=policy.id,
                icd_id=chosen_icd.id,
                condition_name=chosen_icd.description,
                rule_type=random.choice(list(RuleType)),
                waiting_period_months=random.choice([6, 12, 24]),
                max_payout_limit=Decimal(random.choice(["50000.00", "100000.00"])),
            )
            session.add(rule)
            session.flush()

            # 4. Generate Claims targeting this policy
            for c in range(2):
                patient = random.choice([holder.name, dependent.name])
                admission_dt = fake.date_between(
                    start_date=policy.start_date, end_date=policy.end_date
                )
                days_stayed = random.randint(2, 7)
                discharge_dt = admission_dt + timedelta(days=days_stayed)

                claim = Claim(
                    policy_id=policy.id,
                    patient_name=patient,
                    status=ClaimStatus.INITIATED,
                    fraud_score=Decimal("0.00"),
                )
                session.add(claim)
                session.flush()

                claim_icd = random.choice(icd_pool)
                med_detail = ClaimMedicalDetail(
                    claim_id=claim.id,
                    hospital_id=f"HOSP-{random.randint(1000, 9999)}",
                    hospital_name=f"{fake.company()} Healthcare",
                    hospital_type=random.choice(list(HospitalType)),
                    admission_date=admission_dt,
                    discharge_date=discharge_dt,
                    icd_id=claim_icd.id,
                    procedure_name=fake.sentence(nb_words=3),
                    room_category_used=random.choice(
                        ["Deluxe Room", "Twin Sharing", "ICU"]
                    ),
                )
                session.add(med_detail)

                # Create structured audit numbers
                # Let's purposefully make some claims exceed the 5000.00 room cap to test your AI agent
                multiplier = random.choice([4500, 5500])
                req_hosp = Decimal(str(days_stayed * multiplier))
                req_pre = Decimal(str(random.randint(2000, 5000)))
                req_post = Decimal(str(random.randint(3000, 7000)))
                req_total = req_hosp + req_pre + req_post

                financial = ClaimFinancial(
                    claim_id=claim.id,
                    requested_hospitalization=req_hosp,
                    requested_pre_hospitalization=req_pre,
                    requested_post_hospitalization=req_post,
                    requested_total=req_total,
                )
                session.add(financial)

        # Commit everything permanently to PostgreSQL
        session.commit()
        print("PostgreSQL database seeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred during seeding. Session rolled back: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
