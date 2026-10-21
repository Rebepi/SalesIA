from uuid import uuid4
from tests.support.in_memory_outbox import (
    InMemoryOutboxRepository,
    InboxDeduplicator,
    OutboxDispatcher,
    OutboxRecord
)


def test_outbox_save_and_retrieve_pending():
    repo = InMemoryOutboxRepository()
    record = OutboxRecord(
        event_id=uuid4(),
        event_type="test.event",
        company_id=uuid4(),
        payload={"message": "hello"}
    )
    repo.save(record)

    pending = repo.get_pending()
    assert len(pending) == 1
    assert pending[0].event_id == record.event_id
    assert pending[0].status == "pending"


def test_outbox_dispatcher_success():
    repo = InMemoryOutboxRepository()
    dedup = InboxDeduplicator()
    record = OutboxRecord(
        event_id=uuid4(),
        event_type="order.placed",
        company_id=uuid4(),
        payload={"amount": "150.00"}
    )
    repo.save(record)

    published = []

    def mock_publisher(rec: OutboxRecord) -> bool:
        published.append(rec)
        return True

    dispatcher = OutboxDispatcher(
        repository=repo,
        deduplicator=dedup,
        publisher_func=mock_publisher
    )
    count = dispatcher.dispatch_batch()

    assert count == 1
    assert len(published) == 1
    assert repo.get_by_id(record.event_id).status == "published"
    assert dedup.is_processed(record.event_id)


def test_outbox_deduplication_prevents_duplicate_processing():
    repo = InMemoryOutboxRepository()
    dedup = InboxDeduplicator()
    event_id = uuid4()
    record = OutboxRecord(
        event_id=event_id,
        event_type="payment.captured",
        company_id=uuid4(),
        payload={"payment_id": "P-1"}
    )
    repo.save(record)

    call_count = 0

    def publisher(rec: OutboxRecord) -> bool:
        nonlocal call_count
        call_count += 1
        return True

    dispatcher = OutboxDispatcher(
        repository=repo,
        deduplicator=dedup,
        publisher_func=publisher
    )

    dispatcher.dispatch_batch()
    assert call_count == 1

    record.status = "pending"
    repo.save(record)

    dispatcher.dispatch_batch()
    assert call_count == 1


def test_outbox_retry_and_dead_letter():
    repo = InMemoryOutboxRepository()
    dedup = InboxDeduplicator()
    record = OutboxRecord(
        event_id=uuid4(),
        event_type="integration.failed",
        company_id=uuid4(),
        payload={}
    )
    repo.save(record)

    def failing_publisher(rec: OutboxRecord) -> bool:
        return False

    dispatcher = OutboxDispatcher(
        repository=repo,
        deduplicator=dedup,
        publisher_func=failing_publisher
    )

    for _ in range(5):
        dispatcher.dispatch_batch()

    rec = repo.get_by_id(record.event_id)
    assert rec.retry_count == 5
    assert rec.status == "dead_letter"
