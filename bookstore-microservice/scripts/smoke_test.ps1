$ErrorActionPreference = "Stop"

Write-Host "[1/6] Create book..."
$bookBody = @{ title = "DDD Distilled"; author = "Vaughn Vernon"; price = "29.99"; stock = 30 } | ConvertTo-Json
$book = Invoke-RestMethod -Uri "http://127.0.0.1:8003/books/" -Method Post -ContentType "application/json" -Body $bookBody

Write-Host "[2/6] Create customer..."
$customerBody = @{ name = "Smoke User"; email = ("smoke" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + "@example.com") } | ConvertTo-Json
$customer = Invoke-RestMethod -Uri "http://127.0.0.1:8002/customers/" -Method Post -ContentType "application/json" -Body $customerBody

Write-Host "[3/6] Resolve cart id..."
$customerCart = Invoke-RestMethod -Uri ("http://127.0.0.1:8005/carts/{0}/" -f $customer.id) -Method Get

Write-Host "[4/6] Add item to cart..."
$addBody = @{ cart_id = $customerCart.cart_id; book_id = $book.id; quantity = 2 } | ConvertTo-Json
$item = Invoke-RestMethod -Uri "http://127.0.0.1:8005/cart-items/" -Method Post -ContentType "application/json" -Body $addBody

Write-Host "[5/6] Verify cart data..."
$cart = Invoke-RestMethod -Uri ("http://127.0.0.1:8005/carts/{0}/" -f $customer.id) -Method Get
if (-not $cart.items -or $cart.items.Count -lt 1) {
    throw "Cart is empty after add-item step."
}

Write-Host "[6/7] Verify books page..."
$booksPage = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/books/" -Method Get
if ($booksPage.StatusCode -ne 200) {
    throw "Books page failed with status $($booksPage.StatusCode)"
}

Write-Host "[7/7] Verify cart page..."
$cartPage = Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:8000/cart/{0}/" -f $customer.id) -Method Get
if ($cartPage.StatusCode -ne 200) {
    throw "Cart page failed with status $($cartPage.StatusCode)"
}

Write-Host "SMOKE TEST PASSED"
Write-Host ("BOOK_ID=" + $book.id)
Write-Host ("CUSTOMER_ID=" + $customer.id)
Write-Host ("CART_ITEM_ID=" + $item.id)
Write-Host ("CART_COUNT=" + $cart.items.Count)
Write-Host ("BOOKS_PAGE_STATUS=" + $booksPage.StatusCode)
Write-Host ("CART_PAGE_STATUS=" + $cartPage.StatusCode)
