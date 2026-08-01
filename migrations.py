async def m001_initial(db):
    """
    Initial giftcards table (Phase 1 schema).
    """
    await db.execute(f"""
        CREATE TABLE nfcgiftcards.giftcards (
            id TEXT PRIMARY KEY,
            wallet_id TEXT NOT NULL,
            withdraw_id TEXT NOT NULL,
            lnurl TEXT,
            amount INTEGER NOT NULL,
            uses INTEGER NOT NULL DEFAULT 1,
            redeemed INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT {db.timestamp_column_default},
            expires_at TIMESTAMP,
            note TEXT
        );
    """)


async def m002_balance_and_k1(db):
    """
    Phase 2: Switch from fixed-use vouchers to balance tracking.
    SQLite DROP COLUMN is unreliable, so we recreate the table.
    """
    await db.execute(f"""
        CREATE TABLE nfcgiftcards.giftcards_new (
            id TEXT PRIMARY KEY,
            wallet_id TEXT NOT NULL,
            lnurl TEXT,
            amount INTEGER NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            k1 TEXT,
            created_at TIMESTAMP DEFAULT {db.timestamp_column_default},
            expires_at TIMESTAMP,
            note TEXT
        );
    """)

    # Migrate existing data: use id as k1 (already unique and random)
    await db.execute("""
        INSERT INTO nfcgiftcards.giftcards_new
            (id, wallet_id, lnurl, amount, balance, k1, created_at, expires_at, note)
        SELECT
            id,
            wallet_id,
            lnurl,
            amount,
            amount,
            id,
            created_at,
            expires_at,
            note
        FROM nfcgiftcards.giftcards;
    """)

    await db.execute("DROP TABLE nfcgiftcards.giftcards;")
    await db.execute("ALTER TABLE nfcgiftcards.giftcards_new RENAME TO giftcards;")
