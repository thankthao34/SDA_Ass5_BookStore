# Architecture Diagram

## System Context

```mermaid
flowchart LR
    Client[Browser] --> Gateway[api-gateway :8000]

    Gateway --> Customer[customer-service :8000]
    Gateway --> Book[book-service :8000]
    Gateway --> Cart[cart-service :8000]

    Customer --> Cart
    Cart --> Book

    Customer --> CustomerDB[(customer db.sqlite3)]
    Book --> BookDB[(book db.sqlite3)]
    Cart --> CartDB[(cart db.sqlite3)]
    Gateway --> GatewayDB[(gateway db.sqlite3)]
```

## Design Notes

- Microservice boundary is separated by process and database.
- Inter-service communication uses HTTP REST via requests.
- customer-service POST /customers/ triggers cart-service POST /carts/.
- cart-service POST /cart-items/ validates book existence through book-service GET /books/.
- api-gateway renders HTML pages and delegates business actions to backend services.
