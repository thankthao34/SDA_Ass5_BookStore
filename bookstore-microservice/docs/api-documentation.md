# API Documentation

## customer-service (http://localhost:8001)

### GET /customers/
- Description: List all customers.
- Response 200:
```json
[
  {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  }
]
```

### POST /customers/
- Description: Create customer and auto-create cart in cart-service.
- Request body:
```json
{
  "name": "Alice",
  "email": "alice@example.com"
}
```
- Response 201:
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

## book-service (http://localhost:8002)

### GET /books/
- Description: List all books.

### POST /books/
- Description: Create a book.
- Request body:
```json
{
  "title": "Clean Code",
  "author": "Robert Martin",
  "price": "30.00",
  "stock": 100
}
```

## cart-service (http://localhost:8003)

### POST /carts/
- Description: Create a cart for customer_id.
- Request body:
```json
{
  "customer_id": 1
}
```

### POST /cart-items/
- Description: Add item to cart after validating book existence.
- Request body option A:
```json
{
  "cart": 1,
  "book_id": 2,
  "quantity": 3
}
```
- Request body option B:
```json
{
  "customer_id": 1,
  "book_id": 2,
  "quantity": 3
}
```

### GET /carts/{customer_id}/
- Description: List cart items by customer id.

## api-gateway (http://localhost:8000)

### GET /customers/
- HTML page for customer creation/listing.

### GET /books/
- HTML page for book creation/listing.

### GET /cart/{customer_id}/
- HTML page for add/view cart items.
