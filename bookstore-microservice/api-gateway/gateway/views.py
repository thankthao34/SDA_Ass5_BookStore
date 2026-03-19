import os
import json
from urllib.parse import urlencode
from decimal import Decimal
from datetime import datetime

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:8000")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8000")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
SHIP_SERVICE_URL = os.getenv("SHIP_SERVICE_URL", "http://ship-service:8000")
RECOMMENDER_URL = os.getenv("RECOMMENDER_URL", "http://recommender-ai-service:8000")
STAFF_SERVICE_URL = os.getenv("STAFF_SERVICE_URL", "http://staff-service:8000")
MANAGER_SERVICE_URL = os.getenv("MANAGER_SERVICE_URL", "http://manager-service:8000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8000")
PAY_SERVICE_URL = os.getenv("PAY_SERVICE_URL", "http://pay-service:8000")
COMMENT_RATE_SERVICE_URL = os.getenv("COMMENT_RATE_SERVICE_URL", "http://comment-rate-service:8000")

ORDER_STATUS_CHOICES = ["PENDING", "CONFIRMED", "CANCELLED"]
SHIPMENT_STATUS_CHOICES = ["PENDING", "PROCESSING", "SHIPPED", "IN_TRANSIT", "DELIVERED", "CANCELLED"]


def _build_login_redirect(request):
	query = urlencode({"next": request.get_full_path()})
	return redirect(f"{reverse('login')}?{query}")


def _get_profile(user):
	profile, _ = UserProfile.objects.get_or_create(
		user=user,
		defaults={"role": "customer"},
	)
	return profile


def _authorize_request(request, allowed_roles=None, customer_id=None):
	if not request.user.is_authenticated:
		return None, _build_login_redirect(request)

	profile = _get_profile(request.user)

	if allowed_roles and profile.role not in allowed_roles:
		messages.error(request, "You do not have permission to access this page.")
		return profile, redirect("home")

	if customer_id is not None and profile.role == "customer" and profile.customer_id != customer_id:
		messages.error(request, "Customers can only access their own shopping data.")
		return profile, redirect("home")

	return profile, None


def _normalize_text(value):
	return str(value or "").casefold()


def _matches_keyword(item, fields, keyword):
	needle = _normalize_text(keyword)
	if not needle:
		return True

	for field in fields:
		if needle in _normalize_text(item.get(field)):
			return True
	return False


def _can_customer_review_book(customer_id, book_id):
	try:
		orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", timeout=6)
		orders_response.raise_for_status()
		orders = orders_response.json()
	except requests.RequestException as exc:
		return False, f"Cannot verify purchase history: {exc}"

	has_purchased = False
	for order in orders:
		items = order.get("items", [])
		has_book = any(str(item.get("book_id")) == str(book_id) for item in items)
		if not has_book:
			continue

		has_purchased = True
		order_id = order.get("id")
		if not order_id:
			continue

		try:
			shipment_response = requests.get(f"{SHIP_SERVICE_URL}/shipments/{order_id}/", timeout=6)
			if shipment_response.status_code == 404:
				continue
			shipment_response.raise_for_status()
			shipment = shipment_response.json()
			if shipment.get("status") == "DELIVERED":
				return True, None
		except requests.RequestException as exc:
			return False, f"Cannot verify shipment status: {exc}"

	if not has_purchased:
		return False, "Ban can mua sach nay truoc khi danh gia."

	return False, "Ban chi duoc danh gia sau khi don hang da giao thanh cong (DELIVERED)."


def login_view(request):
	if request.user.is_authenticated:
		return redirect("home")

	error = None
	next_url = request.GET.get("next", reverse("home"))

	if request.method == "POST":
		next_url = request.POST.get("next") or reverse("home")
		username = request.POST.get("username", "").strip()
		password = request.POST.get("password", "")
		user = authenticate(request, username=username, password=password)
		if user is None:
			error = "Invalid username or password."
		else:
			login(request, user)
			messages.success(request, "Login successful.")
			return redirect(next_url)

	return render(request, "login.html", {"error": error, "next": next_url})


def logout_view(request):
	if request.user.is_authenticated:
		logout(request)
	messages.info(request, "You have been logged out.")
	return redirect("login")


def profile_home(request):
	profile, auth_response = _authorize_request(request)
	if auth_response:
		return auth_response

	return render(
		request,
		"home.html",
		{
			"profile": profile,
		},
	)


def customer_list(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin", "staff", "manager"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()

	message = None
	error = None

	if request.method == "POST":
		payload = {
			"name": request.POST.get("name", "").strip(),
			"email": request.POST.get("email", "").strip(),
			"phone": request.POST.get("phone", "").strip(),
			"address": request.POST.get("address", "").strip(),
		}
		try:
			response = requests.post(f"{CUSTOMER_SERVICE_URL}/customers/", json=payload, timeout=5)
			if response.status_code < 400:
				message = "Customer created and cart auto-initialized."
			else:
				error = f"Cannot create customer: {response.text}"
		except requests.RequestException as exc:
			error = f"Customer service unavailable: {exc}"

	try:
		response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/", timeout=5)
		response.raise_for_status()
		customers = response.json()
		if search_query:
			customers = [
				customer
				for customer in customers
				if _matches_keyword(customer, ["id", "name", "email", "phone", "address"], search_query)
			]
		if not customers and not error:
			if search_query:
				message = f'No customers found for "{search_query}".'
			else:
				message = "No customers yet. Create one to start shopping flows."
	except requests.RequestException as exc:
		customers = []
		error = f"Cannot load customers: {exc}"

	return render(
		request,
		"customers.html",
		{
			"customers": customers,
			"search_query": search_query,
			"message": message,
			"error": error,
		},
	)


def book_list(request):
	profile, auth_response = _authorize_request(request)
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()

	message = None
	error = None
	can_manage_books = profile.role in {"admin", "staff", "manager"}
	can_customer_add_to_cart = profile.role == "customer" and bool(profile.customer_id)

	if request.method == "POST":
		action = request.POST.get("action", "create_book")

		if action == "add_to_cart":
			if not can_customer_add_to_cart:
				messages.error(request, "Only customers can add items to cart.")
				return redirect("books")

			try:
				cart_response = requests.get(f"{CART_SERVICE_URL}/carts/{profile.customer_id}/", timeout=5)
				cart_response.raise_for_status()
				cart_data = cart_response.json()
			except requests.RequestException as exc:
				error = f"Cannot resolve your cart: {exc}"
			else:
				payload = {
					"cart_id": cart_data.get("cart_id"),
					"book_id": request.POST.get("book_id", "").strip(),
					"quantity": request.POST.get("quantity", "1").strip(),
				}
				search_q = request.POST.get("q", "").strip()
				try:
					response = requests.post(f"{CART_SERVICE_URL}/cart-items/", json=payload, timeout=5)
					if response.status_code < 400:
						messages.success(request, "Book added to your cart.")
						if search_q:
							return redirect(f"{reverse('books')}?{urlencode({'q': search_q})}")
						return redirect("books")
					error = f"Cannot add to cart: {response.text}"
				except requests.RequestException as exc:
					error = f"Cart service unavailable: {exc}"

		else:
			if not can_manage_books:
				messages.error(request, "Only staff, manager, or admin can create books.")
				return redirect("books")

			payload = {
				"title": request.POST.get("title", "").strip(),
				"author": request.POST.get("author", "").strip(),
				"price": request.POST.get("price", "0"),
				"stock": request.POST.get("stock", "0"),
			}
			try:
				response = requests.post(f"{BOOK_SERVICE_URL}/books/", json=payload, timeout=5)
				if response.status_code < 400:
					return redirect("books")
				error = f"Cannot create book: {response.text}"
			except requests.RequestException as exc:
				error = f"Book service unavailable: {exc}"

	try:
		response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
		response.raise_for_status()
		books = response.json()
		if search_query:
			books = [
				book
				for book in books
				if _matches_keyword(
					book,
					["id", "title", "author", "description", "price", "stock", "catalog_id"],
					search_query,
				)
			]
		if not books:
			if search_query:
				message = f'No books found for "{search_query}".'
			else:
				message = "No books yet. Create your first title below."
	except requests.RequestException as exc:
		books = []
		error = f"Cannot load books: {exc}"

	return render(
		request,
		"books.html",
		{
			"books": books,
			"search_query": search_query,
			"can_manage_books": can_manage_books,
			"can_customer_add_to_cart": can_customer_add_to_cart,
			"message": message,
			"error": error,
		},
	)


def book_detail(request, book_id):
	profile, auth_response = _authorize_request(request)
	if auth_response:
		return auth_response

	error = None
	review_block_reason = None

	try:
		book_response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=6)
		if book_response.status_code == 404:
			return render(
				request,
				"book_detail.html",
				{
					"book": None,
					"reviews": [],
					"stats": {"avg_rating": 0, "total": 0},
					"error": "Book not found.",
				},
			)
		book_response.raise_for_status()
		book = book_response.json()
	except requests.RequestException as exc:
		return render(
			request,
			"book_detail.html",
			{
				"book": None,
				"reviews": [],
				"stats": {"avg_rating": 0, "total": 0},
				"error": f"Cannot load book details: {exc}",
			},
		)

	if request.method == "POST":
		if profile.role != "customer" or not profile.customer_id:
			error = "Only customers can submit reviews."
		else:
			can_review_now, reason = _can_customer_review_book(profile.customer_id, book_id)
			if not can_review_now:
				error = reason
			else:
				payload = {
					"customer_id": profile.customer_id,
					"book_id": book_id,
					"rating": request.POST.get("rating", "").strip(),
					"comment": request.POST.get("comment", "").strip(),
				}
				try:
					response = requests.post(f"{COMMENT_RATE_SERVICE_URL}/reviews/", json=payload, timeout=6)
					if response.status_code < 400:
						messages.success(request, "Review submitted successfully.")
						return redirect("book-detail", book_id=book_id)
					error = f"Cannot submit review: {response.text}"
				except requests.RequestException as exc:
					error = f"Comment-rate service unavailable: {exc}"

	try:
		reviews_response = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/book/{book_id}/", timeout=6)
		reviews_response.raise_for_status()
		reviews = reviews_response.json()
	except requests.RequestException as exc:
		reviews = []
		error = error or f"Cannot load reviews: {exc}"

	try:
		stats_response = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/stats/{book_id}/", timeout=6)
		if stats_response.status_code < 400:
			stats = stats_response.json()
		else:
			stats = {"avg_rating": 0, "total": 0}
	except requests.RequestException:
		stats = {"avg_rating": 0, "total": 0}

	can_review = False
	if profile.role == "customer" and profile.customer_id:
		has_existing_review = any(str(review.get("customer_id")) == str(profile.customer_id) for review in reviews)
		if has_existing_review:
			review_block_reason = "Ban da danh gia sach nay."
		else:
			can_review, review_block_reason = _can_customer_review_book(profile.customer_id, book_id)
	else:
		review_block_reason = "Chi tai khoan customer moi co the danh gia sach."

	return render(
		request,
		"book_detail.html",
		{
			"book": book,
			"reviews": reviews,
			"stats": stats,
			"can_review": can_review,
			"review_block_reason": review_block_reason,
			"error": error,
		},
	)


def view_cart(request, customer_id):
	profile, auth_response = _authorize_request(request, customer_id=customer_id)
	if auth_response:
		return auth_response

	message = None
	error = None
	cart = None
	items = []
	cart_total = Decimal("0")
	can_edit_cart = profile.role == "customer" and profile.customer_id == customer_id

	try:
		cart_response = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=5)
		if cart_response.status_code == 404:
			cart = None
		else:
			cart_response.raise_for_status()
			cart = cart_response.json()
			items = cart.get("items", [])
			for item in items:
				price = Decimal(str(item.get("price_snapshot", 0)))
				qty = int(item.get("quantity", 0) or 0)
				cart_total += price * qty
			if not items:
				message = "This cart is empty. Add a book to get started."
	except requests.RequestException as exc:
		error = f"Cannot load cart: {exc}"

	if request.method == "POST":
		if not can_edit_cart:
			error = "Only the owner customer can modify this cart."
			return redirect("cart", customer_id=customer_id)

		action = request.POST.get("action", "add_item")

		if not cart:
			error = "Cart not found for this customer. Create customer first."
			return render(
				request,
				"cart.html",
				{
					"customer_id": customer_id,
					"items": items,
					"books": [],
					"message": message,
					"error": error,
				},
			)

		if action == "checkout":
			if not items:
				error = "Cannot checkout an empty cart."
			else:
				payload = {
					"customer_id": customer_id,
					"cart_id": cart.get("cart_id"),
					"pay_method": request.POST.get("pay_method", "cod"),
					"ship_address": request.POST.get("ship_address", "").strip(),
					"items": [
						{
							"book_id": item.get("book_id"),
							"quantity": item.get("quantity"),
						}
						for item in items
					],
				}
				try:
					response = requests.post(f"{ORDER_SERVICE_URL}/orders/", json=payload, timeout=8)
					if response.status_code >= 400:
						error = f"Checkout failed: {response.text}"
					else:
						messages.success(request, "Order created successfully.")
						return redirect("orders", customer_id=customer_id)
				except requests.RequestException as exc:
					error = f"Order service unavailable: {exc}"
		else:
			if action == "update_item":
				item_id = request.POST.get("item_id", "").strip()
				new_quantity = request.POST.get("quantity", "1").strip()
				if not item_id:
					error = "Missing cart item id."
				else:
					try:
						response = requests.put(
							f"{CART_SERVICE_URL}/cart-items/{item_id}/",
							json={"quantity": new_quantity},
							timeout=5,
						)
						if response.status_code >= 400:
							error = f"Cannot update item: {response.text}"
						else:
							messages.success(request, "Cart item updated successfully.")
							return redirect("cart", customer_id=customer_id)
					except requests.RequestException as exc:
						error = f"Cart service unavailable: {exc}"
			elif action == "remove_item":
				item_id = request.POST.get("item_id", "").strip()
				if not item_id:
					error = "Missing cart item id."
				else:
					try:
						response = requests.delete(f"{CART_SERVICE_URL}/cart-items/{item_id}/", timeout=5)
						if response.status_code >= 400:
							error = f"Cannot remove item: {response.text}"
						else:
							messages.success(request, "Item removed from cart.")
							return redirect("cart", customer_id=customer_id)
					except requests.RequestException as exc:
						error = f"Cart service unavailable: {exc}"
			else:
				payload = {
					"cart_id": cart.get("cart_id"),
					"book_id": request.POST.get("book_id", "").strip(),
					"quantity": request.POST.get("quantity", "1").strip(),
				}
				try:
					response = requests.post(f"{CART_SERVICE_URL}/cart-items/", json=payload, timeout=5)
					if response.status_code >= 400:
						error = f"Cannot add item: {response.text}"
					else:
						messages.success(request, "Book added to cart.")
						return redirect("cart", customer_id=customer_id)
				except requests.RequestException as exc:
					error = f"Cart service unavailable: {exc}"

	if can_edit_cart:
		try:
			books_response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
			books_response.raise_for_status()
			books = books_response.json()
		except requests.RequestException:
			books = []
	else:
		books = []

	return render(
		request,
		"cart.html",
		{
			"customer_id": customer_id,
			"cart_id": cart.get("cart_id") if cart else None,
			"items": items,
			"cart_total": cart_total,
			"books": books,
			"can_checkout": can_edit_cart,
			"can_edit_cart": can_edit_cart,
			"message": message,
			"error": error,
		},
	)


def manage_orders(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin", "manager"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()

	error = None

	if request.method == "POST":
		order_id = request.POST.get("order_id", "").strip()
		new_status = request.POST.get("status", "").strip()
		if not order_id or new_status not in ORDER_STATUS_CHOICES:
			error = "Invalid order update payload."
		else:
			try:
				response = requests.put(
					f"{ORDER_SERVICE_URL}/orders/{order_id}/status/",
					json={"status": new_status},
					timeout=5,
				)
				if response.status_code < 400:
					messages.success(request, f"Order #{order_id} updated to {new_status}.")
					post_search_query = request.POST.get("q", "").strip()
					if post_search_query:
						return redirect(f"{reverse('manage-orders')}?{urlencode({'q': post_search_query})}")
					return redirect("manage-orders")
				error = f"Cannot update order: {response.text}"
			except requests.RequestException as exc:
				error = f"Order service unavailable: {exc}"

	try:
		response = requests.get(f"{ORDER_SERVICE_URL}/orders/", timeout=5)
		response.raise_for_status()
		orders = response.json()
		if search_query:
			orders = [
				order
				for order in orders
				if _matches_keyword(
					order,
					[
						"id",
						"customer_id",
						"status",
						"pay_method",
						"total_price",
						"payment_id",
						"shipment_id",
						"created_at",
					],
					search_query,
				)
			]
	except requests.RequestException as exc:
		orders = []
		error = f"Cannot load orders: {exc}"

	return render(
		request,
		"manage_orders.html",
		{
			"orders": orders,
			"search_query": search_query,
			"status_choices": ORDER_STATUS_CHOICES,
			"error": error,
		},
	)


def manage_shipments(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin", "manager", "staff"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()

	error = None

	if request.method == "POST":
		shipment_id = request.POST.get("shipment_id", "").strip()
		new_status = request.POST.get("status", "").strip()
		if not shipment_id or new_status not in SHIPMENT_STATUS_CHOICES:
			error = "Invalid shipment update payload."
		else:
			try:
				response = requests.put(
					f"{SHIP_SERVICE_URL}/shipments/{shipment_id}/status/",
					json={"status": new_status},
					timeout=5,
				)
				if response.status_code < 400:
					messages.success(request, f"Shipment #{shipment_id} updated to {new_status}.")
					post_search_query = request.POST.get("q", "").strip()
					if post_search_query:
						return redirect(f"{reverse('manage-shipments')}?{urlencode({'q': post_search_query})}")
					return redirect("manage-shipments")
				error = f"Cannot update shipment: {response.text}"
			except requests.RequestException as exc:
				error = f"Ship service unavailable: {exc}"

	try:
		response = requests.get(f"{SHIP_SERVICE_URL}/shipments/", timeout=5)
		response.raise_for_status()
		shipments = response.json()
		if search_query:
			shipments = [
				shipment
				for shipment in shipments
				if _matches_keyword(
					shipment,
					["id", "order_id", "address", "tracking_code", "status", "created_at"],
					search_query,
				)
			]
	except requests.RequestException as exc:
		shipments = []
		error = f"Cannot load shipments: {exc}"

	return render(
		request,
		"manage_shipments.html",
		{
			"shipments": shipments,
			"search_query": search_query,
			"status_choices": SHIPMENT_STATUS_CHOICES,
			"error": error,
		},
	)


def order_history(request, customer_id):
	profile, auth_response = _authorize_request(request, customer_id=customer_id)
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()

	if request.method == "POST":
		post_search_query = request.POST.get("q", "").strip()
		if profile.role != "customer" or profile.customer_id != customer_id:
			messages.error(request, "Only the owner customer can submit reviews from this page.")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		order_id = request.POST.get("order_id", "").strip()
		book_id = request.POST.get("book_id", "").strip()
		rating = request.POST.get("rating", "").strip()
		comment = request.POST.get("comment", "").strip()

		if not order_id or not book_id or not rating:
			messages.error(request, "Order ID, Book ID, and rating are required.")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		try:
			orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", timeout=6)
			orders_response.raise_for_status()
			orders = orders_response.json()
		except requests.RequestException as exc:
			messages.error(request, f"Cannot verify order before review: {exc}")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		target_order = next((order for order in orders if str(order.get("id")) == order_id), None)
		if not target_order:
			messages.error(request, "Order not found.")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		has_book_in_order = any(str(item.get("book_id")) == book_id for item in target_order.get("items", []))
		if not has_book_in_order:
			messages.error(request, "This book is not in the selected order.")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		try:
			shipment_response = requests.get(f"{SHIP_SERVICE_URL}/shipments/{order_id}/", timeout=6)
			if shipment_response.status_code == 404:
				messages.error(request, "Shipment record not found for this order.")
				if post_search_query:
					return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
				return redirect("orders", customer_id=customer_id)
			shipment_response.raise_for_status()
			shipment = shipment_response.json()
		except requests.RequestException as exc:
			messages.error(request, f"Cannot verify shipment status: {exc}")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		if shipment.get("status") != "DELIVERED":
			messages.error(request, "You can review only after shipment is DELIVERED.")
			if post_search_query:
				return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
			return redirect("orders", customer_id=customer_id)

		payload = {
			"customer_id": customer_id,
			"book_id": book_id,
			"rating": rating,
			"comment": comment,
		}
		try:
			review_response = requests.post(f"{COMMENT_RATE_SERVICE_URL}/reviews/", json=payload, timeout=6)
			if review_response.status_code < 400:
				messages.success(request, "Review submitted successfully.")
			else:
				messages.error(request, f"Cannot submit review: {review_response.text}")
		except requests.RequestException as exc:
			messages.error(request, f"Comment-rate service unavailable: {exc}")

		if post_search_query:
			return redirect(f"{reverse('orders', args=[customer_id])}?{urlencode({'q': post_search_query})}")
		return redirect("orders", customer_id=customer_id)

	try:
		response = requests.get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", timeout=6)
		response.raise_for_status()
		orders = response.json()

		try:
			shipment_response = requests.get(f"{SHIP_SERVICE_URL}/shipments/", timeout=6)
			shipment_response.raise_for_status()
			shipments = shipment_response.json()
		except requests.RequestException:
			shipments = []

		shipment_by_order = {str(shipment.get("order_id")): shipment for shipment in shipments}

		try:
			reviews_response = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/customer/{customer_id}/", timeout=6)
			reviews_response.raise_for_status()
			customer_reviews = reviews_response.json()
		except requests.RequestException:
			customer_reviews = []

		reviewed_book_ids = {str(review.get("book_id")) for review in customer_reviews}
		can_customer_review = profile.role == "customer" and profile.customer_id == customer_id

		for order in orders:
			shipment = shipment_by_order.get(str(order.get("id")), {})
			shipment_status = shipment.get("status", "UNKNOWN")
			order["shipment_status"] = shipment_status
			order["can_review_order"] = can_customer_review and shipment_status == "DELIVERED"

			for item in order.get("items", []):
				book_id = str(item.get("book_id"))
				item["already_reviewed"] = book_id in reviewed_book_ids
				item["can_review"] = order["can_review_order"] and not item["already_reviewed"]
		if search_query:
			needle = _normalize_text(search_query)
			filtered_orders = []
			for order in orders:
				if _matches_keyword(
					order,
					[
						"id",
						"status",
						"pay_method",
						"total_price",
						"payment_id",
						"shipment_id",
						"shipment_status",
						"created_at",
					],
					search_query,
				):
					filtered_orders.append(order)
					continue

				items = order.get("items", [])
				item_text = " ".join(
					f"{item.get('book_id', '')} {item.get('quantity', '')} {item.get('title_snapshot', '')}"
					for item in items
				)
				if needle in _normalize_text(item_text):
					filtered_orders.append(order)

			orders = filtered_orders

		return render(
			request,
			"orders.html",
			{"orders": orders, "customer_id": customer_id, "search_query": search_query},
		)
	except requests.RequestException as exc:
		return render(
			request,
			"orders.html",
			{
				"orders": [],
				"customer_id": customer_id,
				"search_query": search_query,
				"error": f"Cannot load orders: {exc}",
			},
		)


@csrf_exempt
def create_order(request):
	if not request.user.is_authenticated:
		return JsonResponse({"error": "Authentication required"}, status=401)

	profile = _get_profile(request.user)
	if profile.role not in {"admin", "staff", "manager", "customer"}:
		return JsonResponse({"error": "Permission denied"}, status=403)

	if request.method != "POST":
		return JsonResponse({"error": "Method not allowed"}, status=405)

	try:
		payload = json.loads((request.body or b"{}").decode("utf-8"))
	except json.JSONDecodeError:
		return JsonResponse({"error": "Invalid JSON body"}, status=400)

	if profile.role == "customer":
		payload_customer_id = payload.get("customer_id")
		if payload_customer_id != profile.customer_id:
			return JsonResponse({"error": "Customers can only create their own orders"}, status=403)

	try:
		response = requests.post(f"{ORDER_SERVICE_URL}/orders/", json=payload, timeout=8)
		data = response.json() if response.content else {}
		return JsonResponse(data, status=response.status_code, safe=not isinstance(data, list))
	except ValueError:
		return JsonResponse({"error": "Invalid response from order-service"}, status=502)
	except requests.RequestException as exc:
		return JsonResponse({"error": f"order-service unavailable: {exc}"}, status=503)


def recommendations(request, customer_id):
	_, auth_response = _authorize_request(request, customer_id=customer_id)
	if auth_response:
		return auth_response

	last_error = None
	for timeout_value in (8, 12, 16):
		try:
			response = requests.get(
				f"{RECOMMENDER_URL}/recommendations/{customer_id}/",
				timeout=timeout_value,
			)
			if response.status_code >= 500:
				last_error = requests.HTTPError(
					f"recommender transient HTTP {response.status_code}",
					response=response,
				)
				continue
			response.raise_for_status()
			data = response.json()
			return render(request, "recommendations.html", {"data": data, "customer_id": customer_id})
		except requests.Timeout as exc:
			last_error = exc
			continue
		except requests.RequestException as exc:
			status_code = getattr(getattr(exc, "response", None), "status_code", None)
			if status_code is not None and status_code >= 500:
				last_error = exc
				continue
			last_error = exc
			break

	if last_error is not None:
		return render(
			request,
			"recommendations.html",
			{
				"data": {"recommendations": [], "total": 0},
				"customer_id": customer_id,
				"error": f"Cannot load recommendations: {last_error}",
			},
		)

	return render(
		request,
		"recommendations.html",
		{
			"data": {"recommendations": [], "total": 0},
			"customer_id": customer_id,
			"error": "Cannot load recommendations due to an unexpected gateway condition.",
		},
	)


def staff_directory(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin", "manager"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()
	error = None

	if request.method == "POST":
		payload = {
			"name": request.POST.get("name", "").strip(),
			"email": request.POST.get("email", "").strip(),
			"role": request.POST.get("role", "staff").strip() or "staff",
			"department": request.POST.get("department", "").strip(),
		}
		if not payload["name"] or not payload["email"]:
			error = "Name and email are required."
		else:
			try:
				response = requests.post(f"{STAFF_SERVICE_URL}/staffs/", json=payload, timeout=5)
				if response.status_code < 400:
					messages.success(request, "Staff member created.")
					post_search_query = request.POST.get("q", "").strip()
					if post_search_query:
						return redirect(f"{reverse('staffs')}?{urlencode({'q': post_search_query})}")
					return redirect("staffs")
				error = f"Cannot create staff: {response.text}"
			except requests.RequestException as exc:
				error = f"Staff service unavailable: {exc}"

	try:
		response = requests.get(f"{STAFF_SERVICE_URL}/staffs/", timeout=5)
		response.raise_for_status()
		staffs = response.json()
		if search_query:
			staffs = [
				staff
				for staff in staffs
				if _matches_keyword(
					staff,
					["id", "name", "email", "role", "department", "created_at"],
					search_query,
				)
			]
	except requests.RequestException as exc:
		staffs = []
		error = f"Cannot load staff data: {exc}"

	return render(
		request,
		"staffs.html",
		{
			"staffs": staffs,
			"search_query": search_query,
			"staff_role_choices": ["admin", "staff", "librarian"],
			"error": error,
		},
	)


def manager_directory(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()
	error = None

	if request.method == "POST":
		payload = {
			"name": request.POST.get("name", "").strip(),
			"email": request.POST.get("email", "").strip(),
			"department": request.POST.get("department", "").strip(),
			"level": request.POST.get("level", "junior").strip() or "junior",
		}
		if not payload["name"] or not payload["email"] or not payload["department"]:
			error = "Name, email, and department are required."
		else:
			try:
				response = requests.post(f"{MANAGER_SERVICE_URL}/managers/", json=payload, timeout=5)
				if response.status_code < 400:
					messages.success(request, "Manager created.")
					post_search_query = request.POST.get("q", "").strip()
					if post_search_query:
						return redirect(f"{reverse('managers')}?{urlencode({'q': post_search_query})}")
					return redirect("managers")
				error = f"Cannot create manager: {response.text}"
			except requests.RequestException as exc:
				error = f"Manager service unavailable: {exc}"

	try:
		response = requests.get(f"{MANAGER_SERVICE_URL}/managers/", timeout=5)
		response.raise_for_status()
		managers = response.json()
		if search_query:
			managers = [
				manager
				for manager in managers
				if _matches_keyword(
					manager,
					["id", "name", "email", "department", "level", "created_at"],
					search_query,
				)
			]
	except requests.RequestException as exc:
		managers = []
		error = f"Cannot load manager data: {exc}"

	return render(
		request,
		"managers.html",
		{
			"managers": managers,
			"search_query": search_query,
			"manager_levels": ["junior", "senior", "director"],
			"error": error,
		},
	)


def catalog_overview(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin", "manager", "staff"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()
	error = None

	if request.method == "POST":
		action = request.POST.get("action", "").strip()
		try:
			if action == "create_category":
				payload = {
					"name": request.POST.get("name", "").strip(),
					"description": request.POST.get("description", "").strip(),
					"parent_id": request.POST.get("parent_id", "").strip() or None,
				}
				if not payload["name"]:
					error = "Category name is required."
				else:
					response = requests.post(f"{CATALOG_SERVICE_URL}/categories/", json=payload, timeout=5)
					if response.status_code < 400:
						messages.success(request, "Category created.")
						post_search_query = request.POST.get("q", "").strip()
						if post_search_query:
							return redirect(f"{reverse('catalog')}?{urlencode({'q': post_search_query})}")
						return redirect("catalog")
					error = f"Cannot create category: {response.text}"

			if action == "create_tag":
				payload = {
					"name": request.POST.get("tag_name", "").strip(),
				}
				if not payload["name"]:
					error = "Tag name is required."
				else:
					response = requests.post(f"{CATALOG_SERVICE_URL}/tags/", json=payload, timeout=5)
					if response.status_code < 400:
						messages.success(request, "Tag created.")
						post_search_query = request.POST.get("q", "").strip()
						if post_search_query:
							return redirect(f"{reverse('catalog')}?{urlencode({'q': post_search_query})}")
						return redirect("catalog")
					error = f"Cannot create tag: {response.text}"
		except requests.RequestException as exc:
			error = f"Catalog service unavailable: {exc}"

	try:
		categories_response = requests.get(f"{CATALOG_SERVICE_URL}/categories/", timeout=5)
		categories_response.raise_for_status()
		categories = categories_response.json()
	except requests.RequestException as exc:
		categories = []
		error = f"Cannot load categories: {exc}"

	try:
		tags_response = requests.get(f"{CATALOG_SERVICE_URL}/tags/", timeout=5)
		tags_response.raise_for_status()
		tags = tags_response.json()
	except requests.RequestException as exc:
		tags = []
		error = f"Cannot load tags: {exc}"

	try:
		books_response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
		books_response.raise_for_status()
		books = books_response.json()
	except requests.RequestException:
		books = []

	book_counts = {}
	for book in books:
		catalog_id = book.get("catalog_id")
		if catalog_id is None:
			continue
		book_counts[catalog_id] = book_counts.get(catalog_id, 0) + 1

	for category in categories:
		category["book_count"] = book_counts.get(category.get("id"), 0)

	if search_query:
		categories = [
			category
			for category in categories
			if _matches_keyword(category, ["id", "name", "description", "parent_id", "book_count"], search_query)
		]
		tags = [tag for tag in tags if _matches_keyword(tag, ["id", "name"], search_query)]

	return render(
		request,
		"catalog.html",
		{
			"categories": categories,
			"tags": tags,
			"search_query": search_query,
			"error": error,
		},
	)


def payments_overview(request):
	_, auth_response = _authorize_request(request, allowed_roles={"admin", "manager"})
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()
	error = None

	if request.method == "POST":
		action = request.POST.get("action", "").strip()
		payment_id = request.POST.get("payment_id", "").strip()
		if not payment_id:
			error = "Payment ID is required."
		else:
			try:
				if action == "confirm":
					ref = request.POST.get("transaction_ref", "").strip() or f"GW-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{payment_id}"
					response = requests.put(
						f"{PAY_SERVICE_URL}/payments/{payment_id}/confirm/",
						json={"transaction_ref": ref},
						timeout=5,
					)
					if response.status_code < 400:
						messages.success(request, f"Payment #{payment_id} confirmed.")
						post_search_query = request.POST.get("q", "").strip()
						if post_search_query:
							return redirect(f"{reverse('payments')}?{urlencode({'q': post_search_query})}")
						return redirect("payments")
					error = f"Cannot confirm payment: {response.text}"

				if action == "fail":
					response = requests.put(f"{PAY_SERVICE_URL}/payments/{payment_id}/fail/", json={}, timeout=5)
					if response.status_code < 400:
						messages.success(request, f"Payment #{payment_id} marked as failed.")
						post_search_query = request.POST.get("q", "").strip()
						if post_search_query:
							return redirect(f"{reverse('payments')}?{urlencode({'q': post_search_query})}")
						return redirect("payments")
					error = f"Cannot fail payment: {response.text}"
			except requests.RequestException as exc:
				error = f"Pay service unavailable: {exc}"

	try:
		payments_response = requests.get(f"{PAY_SERVICE_URL}/payments/", timeout=5)
		payments_response.raise_for_status()
		payments = payments_response.json()
	except requests.RequestException as exc:
		payments = []
		error = f"Cannot load payments: {exc}"

	try:
		orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/", timeout=5)
		orders_response.raise_for_status()
		orders = orders_response.json()
	except requests.RequestException:
		orders = []

	order_lookup = {order.get("id"): order for order in orders}
	for payment in payments:
		order = order_lookup.get(payment.get("order_id"), {})
		payment["order_status"] = order.get("status")
		payment["order_customer_id"] = order.get("customer_id")

	if search_query:
		payments = [
			payment
			for payment in payments
			if _matches_keyword(
				payment,
				[
					"id",
					"order_id",
					"method",
					"status",
					"amount",
					"transaction_ref",
					"paid_at",
					"order_status",
					"order_customer_id",
				],
				search_query,
			)
		]

	return render(
		request,
		"payments.html",
		{
			"payments": payments,
			"search_query": search_query,
			"error": error,
		},
	)


def review_hub(request):
	profile, auth_response = _authorize_request(request)
	if auth_response:
		return auth_response

	search_query = request.GET.get("q", "").strip()
	error = None

	if request.method == "POST":
		if profile.role != "customer" or not profile.customer_id:
			error = "Only customers can submit reviews."
			customer_id = ""
		else:
			customer_id = profile.customer_id

		payload = {
			"customer_id": customer_id,
			"book_id": request.POST.get("book_id", "").strip(),
			"rating": request.POST.get("rating", "").strip(),
			"comment": request.POST.get("comment", "").strip(),
		}

		if not payload["customer_id"] or not payload["book_id"] or not payload["rating"]:
			error = "Customer ID, book ID, and rating are required."
		else:
			can_review_now, reason = _can_customer_review_book(payload["customer_id"], payload["book_id"])
			if not can_review_now:
				error = reason
			else:
				try:
					response = requests.post(f"{COMMENT_RATE_SERVICE_URL}/reviews/", json=payload, timeout=6)
					if response.status_code < 400:
						messages.success(request, "Review submitted.")
						post_search_query = request.POST.get("q", "").strip()
						if post_search_query:
							return redirect(f"{reverse('reviews')}?{urlencode({'q': post_search_query})}")
						return redirect("reviews")
					error = f"Cannot create review: {response.text}"
				except requests.RequestException as exc:
					error = f"Comment-rate service unavailable: {exc}"

	try:
		reviews_response = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/", timeout=6)
		reviews_response.raise_for_status()
		reviews = reviews_response.json()
	except requests.RequestException as exc:
		reviews = []
		error = f"Cannot load reviews: {exc}"

	try:
		stats_response = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/stats/", timeout=6)
		stats_response.raise_for_status()
		review_stats = stats_response.json()
	except requests.RequestException:
		review_stats = []

	try:
		books_response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=6)
		books_response.raise_for_status()
		books = books_response.json()
	except requests.RequestException:
		books = []

	book_lookup = {book.get("id"): book for book in books}
	for review in reviews:
		book = book_lookup.get(review.get("book_id"), {})
		review["book_title"] = book.get("title", "Unknown")

	if profile.role == "customer" and profile.customer_id:
		reviews = [review for review in reviews if review.get("customer_id") == profile.customer_id]

	if search_query:
		reviews = [
			review
			for review in reviews
			if _matches_keyword(
				review,
				["id", "customer_id", "book_id", "book_title", "rating", "comment", "created_at"],
				search_query,
			)
		]

	return render(
		request,
		"reviews.html",
		{
			"reviews": reviews,
			"review_stats": review_stats,
			"search_query": search_query,
			"profile": profile,
			"error": error,
		},
	)
