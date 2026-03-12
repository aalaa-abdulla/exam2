"""
Exam 2 - Bookstore API Integration Tests
==========================================
Write your tests below. Each section (Part B and Part D) is marked.
Follow the instructions in each part carefully.


Run your tests with:
    pytest test_bookstore.py -v


Run with coverage:
    pytest test_bookstore.py --cov=bookstore_db --cov=bookstore_app --cov-report=term-missing -v
"""


import pytest
from bookstore_app import app




# ============================================================
# FIXTURE: Test client with isolated database (provided)
# ============================================================


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client with a temporary database."""
    db_path = str(tmp_path / "test_bookstore.db")
    monkeypatch.setattr("bookstore_db.DB_NAME", db_path)


    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client




# ============================================================
# HELPER: Create a book (provided for convenience)
# ============================================================


def create_sample_book(client, title="The Great Gatsby", author="F. Scott Fitzgerald", price=12.99):
    """Helper to create a book and return the response JSON."""
    response = client.post("/books", json={
        "title": title,
        "author": author,
        "price": price,
    })
    return response




# ============================================================
# PART B - Integration Tests (20 marks)
# Write at least 14 tests covering ALL of the following:
#
# POST /books:
#   - Create a valid book (check 201 and response body)
def test_create_valid_book(client):
    response = create_sample_book(client)
    assert response.status_code == 201
    data = response.get_json()
    assert "book" in data
    assert data["book"]["title"] == "The Great Gatsby"

#   - Create with missing title (check 400)
def test_create_with_missing_title(client):
    response = client.post("/books", json={"author": "Author", "price": 10})
    assert response.status_code == 400
    assert "error" in response.get_json()

#   - Create with empty author (check 400)
def test_create_with_empty_author(client):
    response = client.post("/books", json={"title": "Title", "author": "", "price": 10})
    assert response.status_code == 400
    assert "error" in response.get_json()

#   - Create with invalid price (check 400)
def test_create_with_invalid_price(client):
    response = client.post("/books", json={"title": "Title", "author": "Author", "price": -5})
    assert response.status_code == 400
    assert "error" in response.get_json()

#
# GET /books:
#   - List books when empty (check 200, empty list)
def test_list_empty_books(client):
    response = client.get("/books")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data["books"], list)
    assert len(data["books"]) == 0

#   - List books after adding 2+ books (check count)
def test_list_books_after_add_two(client):
    create_sample_book(client, "Book 1")
    create_sample_book(client, "Book 2")
    response = client.get("/books")
    data = response.get_json()
    assert response.status_code == 200
    assert len(data["books"]) >= 2
#
# GET /books/<id>:
#   - Get an existing book (check 200)
def test_get_an_existing_book(client):
    sample_book = create_sample_book(client, "Existing Book")
    book_id = sample_book.get_json()["book"]["id"]
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.get_json()["book"]["title"] == "Existing Book"

#   - Get a non-existing book (check 404)
def test_get_a_non_existing_book(client):
    response = client.get("/books/999")
    assert response.status_code == 404
    assert "error" in response.get_json()
#
# PUT /books/<id>:
#   - Update a book's title (check 200 and new value)
def test_put_update_title(client):
    create = create_sample_book(client)
    book_id = create.get_json()["book"]["id"]
    response = client.put(f"/books/{book_id}", json={"title": "Updated Title"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["book"] is True
    update_response = client.get(f"/books/{book_id}")
    assert update_response.status_code == 200
    assert update_response.get_json()["book"]["title"] == "Updated Title"

#   - Update with invalid price (check 400)
def test_put_update_invalid_price(client):
    create = create_sample_book(client)
    book_id = create.get_json()["book"]["id"]
    response = client.put(f"/books/{book_id}", json={"price": -10})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Price must be positive" in data["error"]

#   - Update a non-existing book (check 404)
def test_put_non_existing_book(client):
    non_existing_id = 11111
    response = client.put(f"/books/{non_existing_id}", json={"title": "New Title"})
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Book not found"
#
# DELETE /books/<id>:
#   - Delete an existing book (check 200, then confirm 404)
def test_delete_existing_book(client):
    create= create_sample_book(client)
    book_id = create.get_json()["book"]["id"]
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 200

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404
    assert "error" in get_response.get_json()
#   - Delete a non-existing book (check 404)
def test_delete_non_existing_book(client):
    non_existing_id = 112233
    response = client.delete(f"/books/{non_existing_id}")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Book not found"
#
# Full workflow:
#   - Create -> Read -> Update -> Read again -> Delete -> Confirm gone
# ============================================================
def test_full_workflow(client):
    #  CREATE
    create_response = create_sample_book(client, title="Workflow Book", author="Author A", price=15.99)
    assert create_response.status_code == 201
    book_id = create_response.get_json()["book"]["id"]

    # READ
    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 200
    assert get_response.get_json()["book"]["title"] == "Workflow Book"

    # UPDATE
    update_response = client.put(f"/books/{book_id}", json={"title": "Updated Workflow Book"})
    assert update_response.status_code == 200
    # update_book returns True, so check for True
    assert update_response.get_json()["book"] is True

    # READ AGAIN
    get_response2 = client.get(f"/books/{book_id}")
    assert get_response2.status_code == 200
    assert get_response2.get_json()["book"]["title"] == "Updated Workflow Book"

    #  DELETE
    delete_response = client.delete(f"/books/{book_id}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["message"] == "Book deleted"

    #  CONFIRM GONE 
    get_response3 = client.get(f"/books/{book_id}")
    assert get_response3.status_code == 404
    assert get_response3.get_json()["error"] == "Book not found"


# TODO: Write your Part B tests here




# ============================================================
# PART D - Coverage (5 marks)
# Run: pytest test_bookstore.py --cov=bookstore_db --cov=bookstore_app --cov-report=term-missing -v
# You must achieve 85%+ coverage across both files.
# If lines are missed, add more tests above to cover them.
# ============================================================




# ============================================================
# BONUS (5 extra marks)
# 1. Add a search endpoint to bookstore_app.py:
#    GET /books/search?q=<query>
#    - Uses search_books() from bookstore_db.py
#    - Returns {"books": [...]} with status 200
#    - Returns {"error": "Search query is required"} with 400 if q is missing
#
# 2. Write 3 integration tests for the search endpoint:
#    - Search by title (partial match)
#    - Search by author (partial match)
#    - Search with no results (empty list)
# ============================================================


# TODO: Write your bonus tests here (optional)
