import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from features import compute_velocity_features, FEATURE_NAMES

Base = declarative_base()

class MockTransaction(Base):
    __tablename__ = "parsed_transactions"
    tx_id = Column(String, primary_key=True)
    origin_account_id = Column(String, index=True)
    vendor_hash = Column(String)
    amount_kes = Column(Float)
    timestamp = Column(DateTime, index=True)
    tx_count_15min = Column(Integer)
    tx_count_24h = Column(Integer)
    time_since_last_tx = Column(Float)

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_cold_start(self):
        session = self.Session()
        now = datetime(2026, 1, 1, 12, 0, 0)
        tsl, c15, c24 = compute_velocity_features(session, "ACC001", now, MockTransaction)
        self.assertEqual(tsl, 0.0)
        self.assertEqual(c15, 0)
        self.assertEqual(c24, 0)
        session.close()

    def test_velocity_with_history(self):
        session = self.Session()
        now = datetime(2026, 1, 1, 12, 0, 0)
        tx1 = MockTransaction(
            tx_id="t1",
            origin_account_id="ACC001",
            vendor_hash="V1",
            amount_kes=100.0,
            timestamp=now - timedelta(minutes=10),
            tx_count_15min=0,
            tx_count_24h=0,
            time_since_last_tx=0.0
        )
        tx2 = MockTransaction(
            tx_id="t2",
            origin_account_id="ACC001",
            vendor_hash="V1",
            amount_kes=200.0,
            timestamp=now - timedelta(hours=2),
            tx_count_15min=0,
            tx_count_24h=0,
            time_since_last_tx=0.0
        )
        session.add_all([tx1, tx2])
        session.commit()

        tsl, c15, c24 = compute_velocity_features(session, "ACC001", now, MockTransaction)
        self.assertAlmostEqual(tsl, 10.0, places=1) # 10 minutes since last tx
        self.assertEqual(c15, 1) # 1 tx in last 15 min
        self.assertEqual(c24, 2) # 2 txs in last 24h
        session.close()

if __name__ == "__main__":
    unittest.main()
