# BookStore Microservice (Assignment 05)

BookStore được tách thành 12 microservice độc lập bằng Django REST Framework, mỗi service có SQLite riêng, chạy đồng bộ qua Docker Compose.

## Danh sách service

- api-gateway (8000): điểm vào duy nhất, render giao diện và proxy đến backend
- staff-service (8001): quản lý nhân viên
- customer-service (8002): quản lý khách hàng, tự tạo cart khi đăng ký
- book-service (8003): quản lý sách và tồn kho
- catalog-service (8004): quản lý category và tag
- cart-service (8005): quản lý giỏ hàng, kiểm tra sách qua book-service
- manager-service (8006): quản lý manager
- order-service (8007): orchestration tạo đơn + gọi pay + ship + giảm stock
- pay-service (8008): xử lý thanh toán
- ship-service (8009): vận chuyển và tracking
- comment-rate-service (8010): review, rating, thống kê
- recommender-ai-service (8011): gợi ý sách rule-based

## Chạy nhanh với Docker

```bash
docker compose up --build
```

## URL gateway demo

- http://localhost:8000/customers/
- http://localhost:8000/books/
- http://localhost:8000/catalog/
- http://localhost:8000/staffs/
- http://localhost:8000/managers/
- http://localhost:8000/cart/1/
- http://localhost:8000/orders/1/
- http://localhost:8000/ops/orders/
- http://localhost:8000/ops/payments/
- http://localhost:8000/ops/shipments/
- http://localhost:8000/reviews/
- http://localhost:8000/recommendations/1/

## Mapping nhanh 8-12 de demo

- order-service (8007): trang `ops/orders/`, cap nhat trang thai don, lien ket qua payment_id/shipment_id.
- pay-service (8008): trang `ops/payments/`, confirm/fail thanh toan va map nguoc ve order/customer.
- ship-service (8009): trang `ops/shipments/`, cap nhat trang thai van chuyen.
- comment-rate-service (8010): trang `reviews/`, tao review, xem danh sach va thong ke rating theo sach.
- recommender-ai-service (8011): trang `recommendations/<customer_id>/`, goi y sach dua tren mua hang + review stats.

## Luồng chính

1. Tạo customer ở customer-service sẽ tự động gọi cart-service tạo cart.
2. Thêm sách bằng book-service (hoặc qua gateway books page).
3. Thêm sách vào cart bằng cart-service (có validate tồn tại và stock sách).
4. Tạo order tại order-service với payload items, service sẽ gọi pay-service và ship-service.
5. order-service gọi book-service giảm stock và gọi cart-service xóa item trong cart sau khi đặt.
6. comment-rate-service cho review sách; recommender-ai-service đề xuất sách theo lịch sử mua.

## Lưu ý vận hành

- Tất cả inter-service URL đọc từ biến môi trường, không hardcode localhost.
- Các lệnh gọi service khác dùng timeout để tránh treo request.
- Migration hiện chạy bằng `migrate --run-syncdb` trong Dockerfile cho từng service.

## Tài liệu tham khảo

- docs/architecture.md
- docs/api-documentation.md
- docs/test-plan.md
- docs/deliverables-checklist.md
