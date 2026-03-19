$ErrorActionPreference = "Stop"

$STAFF_SERVICE_URL = "http://127.0.0.1:8001"
$MANAGER_SERVICE_URL = "http://127.0.0.1:8006"
$BOOK_SERVICE_URL = "http://127.0.0.1:8003"
$CATALOG_SERVICE_URL = "http://127.0.0.1:8004"
$CUSTOMER_SERVICE_URL = "http://127.0.0.1:8002"
$CART_SERVICE_URL = "http://127.0.0.1:8005"
$ORDER_SERVICE_URL = "http://127.0.0.1:8007"
$PAY_SERVICE_URL = "http://127.0.0.1:8008"
$SHIP_SERVICE_URL = "http://127.0.0.1:8009"
$REVIEW_SERVICE_URL = "http://127.0.0.1:8010"
$RECOMMENDER_SERVICE_URL = "http://127.0.0.1:8011"

function Invoke-Api {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $false)]$Payload
    )

    if ($null -eq $Payload) {
        return Invoke-RestMethod -Uri $Url -Method $Method
    }

    $json = $Payload | ConvertTo-Json -Depth 10
    return Invoke-RestMethod -Uri $Url -Method $Method -ContentType "application/json" -Body $json
}

function Get-ByKey {
    param(
        [Parameter(Mandatory = $true)]$Items,
        [Parameter(Mandatory = $true)][string]$Field,
        [Parameter(Mandatory = $true)][string]$Value
    )

    foreach ($item in $Items) {
        if ("$($item.$Field)" -eq $Value) {
            return $item
        }
    }
    return $null
}

Write-Host "[1/12] Filling categories and tags..."
$categoryDefs = @(
    @{ key = "architecture"; name = "Software Architecture"; description = "Design, DDD, clean architecture and microservices." },
    @{ key = "ai"; name = "Data Science and AI"; description = "Machine learning, deep learning and data analytics." },
    @{ key = "fiction"; name = "Fiction and Novel"; description = "Popular fiction, stories and classic novels." },
    @{ key = "business"; name = "Business and Finance"; description = "Business mindset, finance and investing." },
    @{ key = "selfhelp"; name = "Self Development"; description = "Productivity, psychology and personal growth." }
)

$tagDefs = @(
    "microservice", "ddd", "clean-code", "backend", "python", "ai", "machine-learning", "fiction", "finance", "productivity"
)

$existingCategories = Invoke-Api -Method "GET" -Url "$CATALOG_SERVICE_URL/categories/"
$categoryIds = @{}
foreach ($category in $categoryDefs) {
    $found = Get-ByKey -Items $existingCategories -Field "name" -Value $category.name
    if ($null -eq $found) {
        $found = Invoke-Api -Method "POST" -Url "$CATALOG_SERVICE_URL/categories/" -Payload @{
            name = $category.name
            description = $category.description
        }
        $existingCategories += $found
    }
    $categoryIds[$category.key] = $found.id
}

$existingTags = Invoke-Api -Method "GET" -Url "$CATALOG_SERVICE_URL/tags/"
foreach ($tag in $tagDefs) {
    $foundTag = Get-ByKey -Items $existingTags -Field "name" -Value $tag
    if ($null -eq $foundTag) {
        $createdTag = Invoke-Api -Method "POST" -Url "$CATALOG_SERVICE_URL/tags/" -Payload @{ name = $tag }
        $existingTags += $createdTag
    }
}

Write-Host "[2/12] Filling staff and managers..."
$staffDefs = @(
    @{ name = "Admin Nguyen"; email = "admin.nguyen@bookstore.local"; role = "admin"; department = "Operations" },
    @{ name = "Librarian An"; email = "librarian.an@bookstore.local"; role = "librarian"; department = "Library" },
    @{ name = "Staff Binh"; email = "staff.binh@bookstore.local"; role = "staff"; department = "Sales" },
    @{ name = "Staff Chi"; email = "staff.chi@bookstore.local"; role = "staff"; department = "Support" }
)

$managerDefs = @(
    @{ name = "Manager Hoang"; email = "manager.hoang@bookstore.local"; department = "Business"; level = "senior" },
    @{ name = "Director Lan"; email = "director.lan@bookstore.local"; department = "Strategy"; level = "director" },
    @{ name = "Manager Minh"; email = "manager.minh@bookstore.local"; department = "Technology"; level = "junior" }
)

$existingStaffs = Invoke-Api -Method "GET" -Url "$STAFF_SERVICE_URL/staffs/"
foreach ($staff in $staffDefs) {
    $foundStaff = Get-ByKey -Items $existingStaffs -Field "email" -Value $staff.email
    if ($null -eq $foundStaff) {
        $createdStaff = Invoke-Api -Method "POST" -Url "$STAFF_SERVICE_URL/staffs/" -Payload $staff
        $existingStaffs += $createdStaff
    }
}

$existingManagers = Invoke-Api -Method "GET" -Url "$MANAGER_SERVICE_URL/managers/"
foreach ($manager in $managerDefs) {
    $foundManager = Get-ByKey -Items $existingManagers -Field "email" -Value $manager.email
    if ($null -eq $foundManager) {
        $createdManager = Invoke-Api -Method "POST" -Url "$MANAGER_SERVICE_URL/managers/" -Payload $manager
        $existingManagers += $createdManager
    }
}

Write-Host "[3/12] Filling books..."
$bookDefs = @(
    @{ title = "Domain-Driven Design"; author = "Eric Evans"; price = "49.90"; stock = 120; catalog = "architecture"; description = "Strategic and tactical DDD patterns." },
    @{ title = "Clean Architecture"; author = "Robert C. Martin"; price = "39.90"; stock = 120; catalog = "architecture"; description = "Practical architecture principles." },
    @{ title = "Building Microservices"; author = "Sam Newman"; price = "44.50"; stock = 120; catalog = "architecture"; description = "Modern microservice design and operation." },
    @{ title = "Designing Data-Intensive Applications"; author = "Martin Kleppmann"; price = "54.00"; stock = 100; catalog = "architecture"; description = "Reliable, scalable and maintainable systems." },

    @{ title = "Hands-On Machine Learning"; author = "Aurelien Geron"; price = "46.00"; stock = 100; catalog = "ai"; description = "Applied machine learning with practical examples." },
    @{ title = "Deep Learning"; author = "Ian Goodfellow"; price = "59.00"; stock = 90; catalog = "ai"; description = "Foundational deep learning textbook." },
    @{ title = "Python Data Science Handbook"; author = "Jake VanderPlas"; price = "36.00"; stock = 110; catalog = "ai"; description = "Core data science workflows in Python." },
    @{ title = "Practical Statistics for Data Scientists"; author = "Peter Bruce"; price = "33.50"; stock = 110; catalog = "ai"; description = "Statistics concepts for real projects." },

    @{ title = "The Alchemist"; author = "Paulo Coelho"; price = "15.00"; stock = 200; catalog = "fiction"; description = "A journey of destiny and meaning." },
    @{ title = "Norwegian Wood"; author = "Haruki Murakami"; price = "18.00"; stock = 180; catalog = "fiction"; description = "A nostalgic and emotional coming-of-age story." },
    @{ title = "The Midnight Library"; author = "Matt Haig"; price = "17.00"; stock = 180; catalog = "fiction"; description = "A novel about choices and second chances." },
    @{ title = "To Kill a Mockingbird"; author = "Harper Lee"; price = "16.50"; stock = 170; catalog = "fiction"; description = "A classic novel on justice and empathy." },

    @{ title = "The Psychology of Money"; author = "Morgan Housel"; price = "19.50"; stock = 140; catalog = "business"; description = "Behavioral insights for wealth building." },
    @{ title = "Rich Dad Poor Dad"; author = "Robert Kiyosaki"; price = "14.50"; stock = 150; catalog = "business"; description = "Mindset and principles of personal finance." },
    @{ title = "Atomic Habits"; author = "James Clear"; price = "21.00"; stock = 140; catalog = "selfhelp"; description = "Tiny habits for remarkable results." },
    @{ title = "Deep Work"; author = "Cal Newport"; price = "20.00"; stock = 130; catalog = "selfhelp"; description = "Focus strategies for high-value output." },
    @{ title = "Thinking Fast and Slow"; author = "Daniel Kahneman"; price = "24.00"; stock = 120; catalog = "selfhelp"; description = "How the mind makes decisions." },
    @{ title = "Mindset"; author = "Carol Dweck"; price = "18.50"; stock = 140; catalog = "selfhelp"; description = "Growth mindset for learning and success." }
)

$existingBooks = Invoke-Api -Method "GET" -Url "$BOOK_SERVICE_URL/books/"
$createdBooks = @()
$bookByTitle = @{}

foreach ($existingBook in $existingBooks) {
    $bookByTitle[$existingBook.title] = $existingBook
}

foreach ($book in $bookDefs) {
    if (-not $bookByTitle.ContainsKey($book.title)) {
        $created = Invoke-Api -Method "POST" -Url "$BOOK_SERVICE_URL/books/" -Payload @{
            title = $book.title
            author = $book.author
            price = $book.price
            stock = $book.stock
            description = $book.description
            cover_url = ""
            catalog_id = $categoryIds[$book.catalog]
        }
        $createdBooks += $created
        $bookByTitle[$created.title] = $created
    }
}

Write-Host "[4/12] Creating additional customers..."
$timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$customerDefs = @(
    @{ name = "Nguyen Minh Anh"; phone = "0901111111"; address = "District 1, Ho Chi Minh City" },
    @{ name = "Tran Quoc Bao"; phone = "0902222222"; address = "Hai Chau, Da Nang" },
    @{ name = "Le Thu Ha"; phone = "0903333333"; address = "Cau Giay, Ha Noi" },
    @{ name = "Pham Gia Huy"; phone = "0904444444"; address = "Ninh Kieu, Can Tho" },
    @{ name = "Vu Ngoc Linh"; phone = "0905555555"; address = "Bien Hoa, Dong Nai" },
    @{ name = "Do Thanh Nam"; phone = "0906666666"; address = "Hue City" },
    @{ name = "Bui Khanh Van"; phone = "0907777777"; address = "Vung Tau" },
    @{ name = "Hoang Duc Long"; phone = "0908888888"; address = "Thu Duc, Ho Chi Minh City" }
)

$existingCustomers = Invoke-Api -Method "GET" -Url "$CUSTOMER_SERVICE_URL/customers/"
$customers = @()
for ($i = 0; $i -lt $customerDefs.Count; $i++) {
    $def = $customerDefs[$i]
    $email = "customer.$timestamp.$i@example.com"
    $created = Invoke-Api -Method "POST" -Url "$CUSTOMER_SERVICE_URL/customers/" -Payload @{
        name = $def.name
        email = $email
        phone = $def.phone
        address = $def.address
    }
    $customers += $created
}

Write-Host "[5/12] Resolving carts for new customers..."
$cartByCustomerId = @{}
foreach ($customer in $customers) {
    $cart = Invoke-Api -Method "GET" -Url "$CART_SERVICE_URL/carts/$($customer.id)/"
    $cartByCustomerId[$customer.id] = $cart.cart_id
}

Write-Host "[6/12] Creating pending cart items for richer cart pages..."
$pendingCartPlans = @(
    @{ customerIndex = 0; items = @(@{ title = "Deep Learning"; quantity = 1 }, @{ title = "The Midnight Library"; quantity = 1 }) },
    @{ customerIndex = 1; items = @(@{ title = "Atomic Habits"; quantity = 1 }) },
    @{ customerIndex = 2; items = @(@{ title = "The Psychology of Money"; quantity = 1 }, @{ title = "Mindset"; quantity = 2 }) }
)

foreach ($plan in $pendingCartPlans) {
    $customer = $customers[$plan.customerIndex]
    $cartId = $cartByCustomerId[$customer.id]
    foreach ($item in $plan.items) {
        $book = $bookByTitle[$item.title]
        Invoke-Api -Method "POST" -Url "$CART_SERVICE_URL/cart-items/" -Payload @{
            cart_id = $cartId
            book_id = $book.id
            quantity = $item.quantity
        } | Out-Null
    }
}

Write-Host "[7/12] Creating realistic orders..."
$orderPlans = @(
    @{ customerIndex = 0; payMethod = "card"; ship = "District 1, Ho Chi Minh City"; items = @(@{ title = "Domain-Driven Design"; quantity = 1 }, @{ title = "Clean Architecture"; quantity = 1 }) },
    @{ customerIndex = 1; payMethod = "cod"; ship = "Hai Chau, Da Nang"; items = @(@{ title = "Building Microservices"; quantity = 1 }, @{ title = "Designing Data-Intensive Applications"; quantity = 1 }) },
    @{ customerIndex = 2; payMethod = "bank"; ship = "Cau Giay, Ha Noi"; items = @(@{ title = "Hands-On Machine Learning"; quantity = 1 }, @{ title = "Python Data Science Handbook"; quantity = 1 }) },
    @{ customerIndex = 3; payMethod = "cod"; ship = "Ninh Kieu, Can Tho"; items = @(@{ title = "The Alchemist"; quantity = 2 }, @{ title = "The Midnight Library"; quantity = 1 }) },
    @{ customerIndex = 4; payMethod = "card"; ship = "Bien Hoa, Dong Nai"; items = @(@{ title = "The Psychology of Money"; quantity = 1 }, @{ title = "Rich Dad Poor Dad"; quantity = 1 }) },
    @{ customerIndex = 5; payMethod = "bank"; ship = "Hue City"; items = @(@{ title = "Atomic Habits"; quantity = 1 }, @{ title = "Deep Work"; quantity = 1 }) },
    @{ customerIndex = 6; payMethod = "cod"; ship = "Vung Tau"; items = @(@{ title = "Thinking Fast and Slow"; quantity = 1 }, @{ title = "Mindset"; quantity = 1 }) },
    @{ customerIndex = 7; payMethod = "card"; ship = "Thu Duc, Ho Chi Minh City"; items = @(@{ title = "Norwegian Wood"; quantity = 1 }, @{ title = "To Kill a Mockingbird"; quantity = 1 }) },
    @{ customerIndex = 0; payMethod = "bank"; ship = "District 1, Ho Chi Minh City"; items = @(@{ title = "Practical Statistics for Data Scientists"; quantity = 1 }, @{ title = "Hands-On Machine Learning"; quantity = 1 }) },
    @{ customerIndex = 1; payMethod = "card"; ship = "Hai Chau, Da Nang"; items = @(@{ title = "Deep Work"; quantity = 1 }, @{ title = "Atomic Habits"; quantity = 1 }) },
    @{ customerIndex = 2; payMethod = "cod"; ship = "Cau Giay, Ha Noi"; items = @(@{ title = "The Alchemist"; quantity = 1 }, @{ title = "The Midnight Library"; quantity = 1 }) },
    @{ customerIndex = 3; payMethod = "bank"; ship = "Ninh Kieu, Can Tho"; items = @(@{ title = "Domain-Driven Design"; quantity = 1 }, @{ title = "Building Microservices"; quantity = 1 }) }
)

$orders = @()
foreach ($plan in $orderPlans) {
    $customer = $customers[$plan.customerIndex]
    $cartId = $cartByCustomerId[$customer.id]

    $orderItems = @()
    foreach ($item in $plan.items) {
        $book = $bookByTitle[$item.title]
        $orderItems += @{ book_id = $book.id; quantity = $item.quantity }

        Invoke-Api -Method "POST" -Url "$CART_SERVICE_URL/cart-items/" -Payload @{
            cart_id = $cartId
            book_id = $book.id
            quantity = $item.quantity
        } | Out-Null
    }

    $createdOrder = Invoke-Api -Method "POST" -Url "$ORDER_SERVICE_URL/orders/" -Payload @{
        customer_id = $customer.id
        cart_id = $cartId
        pay_method = $plan.payMethod
        ship_address = $plan.ship
        items = $orderItems
    }
    $orders += $createdOrder
}

Write-Host "[8/12] Updating payment statuses..."
for ($i = 0; $i -lt $orders.Count; $i++) {
    $order = $orders[$i]
    try {
        $payment = Invoke-Api -Method "GET" -Url "$PAY_SERVICE_URL/payments/$($order.id)/"
        if ($i % 4 -eq 0) {
            Invoke-Api -Method "PUT" -Url "$PAY_SERVICE_URL/payments/$($payment.id)/fail/" -Payload @{} | Out-Null
        }
        else {
            Invoke-Api -Method "PUT" -Url "$PAY_SERVICE_URL/payments/$($payment.id)/confirm/" -Payload @{ transaction_ref = "TXN-$($order.id)-$timestamp" } | Out-Null
        }
    }
    catch {
    }
}

Write-Host "[9/12] Updating shipment statuses..."
$shipStatusFlow = @("PROCESSING", "SHIPPED", "IN_TRANSIT", "DELIVERED")
for ($i = 0; $i -lt $orders.Count; $i++) {
    $order = $orders[$i]
    try {
        $shipment = Invoke-Api -Method "GET" -Url "$SHIP_SERVICE_URL/shipments/$($order.id)/"
        $statusValue = $shipStatusFlow[$i % $shipStatusFlow.Count]
        Invoke-Api -Method "PUT" -Url "$SHIP_SERVICE_URL/shipments/$($shipment.id)/status/" -Payload @{ status = $statusValue } | Out-Null
    }
    catch {
    }
}

Write-Host "[10/12] Creating reviews..."
$reviewPlans = @(
    @{ customerIndex = 0; title = "Domain-Driven Design"; rating = 5; comment = "Excellent architecture book for serious backend work." },
    @{ customerIndex = 1; title = "Building Microservices"; rating = 4; comment = "Practical and easy to apply in projects." },
    @{ customerIndex = 2; title = "Hands-On Machine Learning"; rating = 5; comment = "Clear examples and strong fundamentals." },
    @{ customerIndex = 3; title = "The Alchemist"; rating = 4; comment = "Simple but inspiring storytelling." },
    @{ customerIndex = 4; title = "The Psychology of Money"; rating = 5; comment = "Great perspective on money behavior." },
    @{ customerIndex = 5; title = "Atomic Habits"; rating = 5; comment = "Very actionable and motivating." },
    @{ customerIndex = 6; title = "Thinking Fast and Slow"; rating = 4; comment = "Dense but extremely valuable." },
    @{ customerIndex = 7; title = "Norwegian Wood"; rating = 4; comment = "Emotional and memorable writing." },
    @{ customerIndex = 0; title = "Practical Statistics for Data Scientists"; rating = 4; comment = "Useful for practical model evaluation." },
    @{ customerIndex = 1; title = "Deep Work"; rating = 5; comment = "Great for improving concentration." },
    @{ customerIndex = 2; title = "The Alchemist"; rating = 4; comment = "Readable and inspiring." },
    @{ customerIndex = 3; title = "Designing Data-Intensive Applications"; rating = 5; comment = "Outstanding systems engineering content." }
)

foreach ($reviewPlan in $reviewPlans) {
    $customer = $customers[$reviewPlan.customerIndex]
    $book = $bookByTitle[$reviewPlan.title]

    $reviewPayload = @{
        customer_id = $customer.id
        book_id = $book.id
        rating = $reviewPlan.rating
        comment = $reviewPlan.comment
    }

    try {
        Invoke-Api -Method "POST" -Url "$REVIEW_SERVICE_URL/reviews/" -Payload $reviewPayload | Out-Null
    }
    catch {
    }
}

Write-Host "[11/12] Checking recommendations..."
for ($i = 0; $i -lt 3; $i++) {
    $customer = $customers[$i]
    $recommend = Invoke-Api -Method "GET" -Url "$RECOMMENDER_SERVICE_URL/recommendations/$($customer.id)/"
    Write-Host ("Customer {0} recommendations: {1}" -f $customer.id, $recommend.total)
}

Write-Host "[12/12] Summary counts..."
$staffList = Invoke-Api -Method "GET" -Url "$STAFF_SERVICE_URL/staffs/"
$managerList = Invoke-Api -Method "GET" -Url "$MANAGER_SERVICE_URL/managers/"
$categoryList = Invoke-Api -Method "GET" -Url "$CATALOG_SERVICE_URL/categories/"
$tagList = Invoke-Api -Method "GET" -Url "$CATALOG_SERVICE_URL/tags/"
$books = Invoke-Api -Method "GET" -Url "$BOOK_SERVICE_URL/books/"
$customerList = Invoke-Api -Method "GET" -Url "$CUSTOMER_SERVICE_URL/customers/"
$orderList = Invoke-Api -Method "GET" -Url "$ORDER_SERVICE_URL/orders/"
$paymentList = Invoke-Api -Method "GET" -Url "$PAY_SERVICE_URL/payments/"
$shipmentList = Invoke-Api -Method "GET" -Url "$SHIP_SERVICE_URL/shipments/"

Write-Host "RICH DATA SEED COMPLETED"
Write-Host ("STAFF_TOTAL=" + $staffList.Count)
Write-Host ("MANAGERS_TOTAL=" + $managerList.Count)
Write-Host ("CATEGORIES_TOTAL=" + $categoryList.Count)
Write-Host ("TAGS_TOTAL=" + $tagList.Count)
Write-Host ("BOOKS_TOTAL=" + $books.Count)
Write-Host ("CUSTOMERS_TOTAL=" + $customerList.Count)
Write-Host ("NEW_CUSTOMERS_CREATED=" + $customers.Count)
Write-Host ("ORDERS_TOTAL=" + $orderList.Count)
Write-Host ("NEW_ORDERS_CREATED=" + $orders.Count)
Write-Host ("PAYMENTS_TOTAL=" + $paymentList.Count)
Write-Host ("SHIPMENTS_TOTAL=" + $shipmentList.Count)
Write-Host ("REVIEWS_CREATED=" + $reviewPlans.Count)
