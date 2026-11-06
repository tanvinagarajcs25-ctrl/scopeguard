import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

# Load credentials from the root .env file
load_dotenv()

API_KEY = os.getenv("HINDSIGHT_API_KEY")
BASE_URL = os.getenv("HINDSIGHT_BASE_URL")

# Use the bank you created in Hindsight Cloud
BANK_ID = "client-sharma-retail"


def main():
    if not API_KEY or not BASE_URL:
        print("ERROR: Check your .env file.")
        return

    client = Hindsight(
        base_url=BASE_URL,
        api_key=API_KEY
    )

    try:
        # 1. RETAIN: Store a test memory
        print("\n1. Testing RETAIN...")

        client.retain(
            bank_id=BANK_ID,
            content="ScopeGuard test: On 12 October, the client requested a wishlist feature. The feature was not included in the signed SOW."
        )

        print("Memory stored successfully!")

        # 2. RECALL: Retrieve the stored memory
        print("\n2. Testing RECALL...")

        results = client.recall(
            bank_id=BANK_ID,
            query="What additional feature did the client request?"
        )

        for memory in results.results:
            print("Retrieved:", memory.text)

        # 3. REFLECT: Generate an insight
        print("\n3. Testing REFLECT...")

        answer = client.reflect(
            bank_id=BANK_ID,
            query="What do you know about the client's additional feature request?"
        )

        print("Reflection:", answer.text)

        print("\nAll three Hindsight operations completed!")

    except Exception as error:
        print("\nHindsight test failed:", error)

    finally:
        client.close()


if __name__ == "__main__":
    main()
