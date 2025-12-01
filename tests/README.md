# Running Unit Tests

## Installation

Install test dependencies:
```bash
pip install pytest pytest-mock
```

Or install all dependencies including tests:
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_booking_client.py -v
pytest tests/test_repository.py -v
pytest tests/test_models.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=api --cov=data --cov=models -v
```

## Test Structure

```
tests/
├── __init__.py
├── test_booking_client.py  # Tests for BookingAPIClient
├── test_repository.py      # Tests for ParticipantRepository
└── test_models.py          # Tests for DTO models
```

## What's Tested

### BookingAPIClient (`test_booking_client.py`)
- ✅ Client initialization and configuration
- ✅ Successful API calls to `/bookings/count`
- ✅ Successful API calls to `/bookings/batch`
- ✅ 404 handling (returns empty list instead of error)
- ✅ Empty response handling
- ✅ HTTP error propagation
- ✅ Trailing slash removal from base URL

### ParticipantRepository (`test_repository.py`)
- ✅ Repository initialization with API client
- ✅ Getting participants by event ID
- ✅ Counting participants by event ID
- ✅ Pagination parameter passing
- ✅ Empty result handling
- ✅ API error propagation
- ✅ Context manager support

### DTO Models (`test_models.py`)
- ✅ `BookingBatchResponse.from_dict()` with complete/minimal data
- ✅ `email` and `name` properties
- ✅ `Event.from_dict()` and date formatting
- ✅ `NotificationMessage.from_json()` with valid/invalid data
- ✅ Error handling for malformed JSON
- ✅ Validation of required fields

## Example Output

```bash
$ pytest tests/ -v

tests/test_booking_client.py::TestBookingAPIClient::test_client_initialization PASSED
tests/test_booking_client.py::TestBookingAPIClient::test_get_bookings_count_success PASSED
tests/test_booking_client.py::TestBookingAPIClient::test_get_bookings_batch_404_returns_empty_list PASSED
tests/test_repository.py::TestParticipantRepository::test_get_participants_by_event_success PASSED
tests/test_repository.py::TestParticipantRepository::test_count_participants_by_event_success PASSED
tests/test_models.py::TestBookingBatchResponse::test_from_dict_complete_data PASSED

========================= 35 passed in 0.52s =========================
```
