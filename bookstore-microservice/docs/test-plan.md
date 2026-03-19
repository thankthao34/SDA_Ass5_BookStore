# Test Plan

## Scope

Validate required Assignment 05 flows:
- Create customer
- Auto create cart
- Add book
- Add item to cart
- View cart
- View books

## Manual Scenarios

1. Create customer via gateway /customers/.
- Expected: customer appears in list.
- Expected: opening /cart/{customer_id}/ shows empty cart without error.

2. Create book via gateway /books/.
- Expected: book appears in catalog list.

3. Add cart item via gateway /cart/{customer_id}/.
- Expected: item added and listed in cart table.

4. Add invalid book_id in cart.
- Expected: error message "Book not found".

## Automated Tests

- customer-service tests:
  - GET customers.
  - POST customer success with mocked cart-service.
  - POST customer failure on cart-service unavailability.

- book-service tests:
  - POST and GET books.

- cart-service tests:
  - POST carts.
  - POST cart-items success with mocked book-service.
  - POST cart-items invalid book.
  - GET carts/{customer_id}.

## Smoke Script Output Target

- BOOKS_PAGE_STATUS=200
- CART_PAGE_STATUS=200
- CART_COUNT >= 1 after add item
