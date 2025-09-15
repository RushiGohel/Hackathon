// Sample Data
const products = [
  { id: 1, title: "Handwoven Basket", category: "Basket", price: 450.0, image: "basket.jpg" },
  { id: 2, title: "Traditional Mask", category: "Mask", price: 800.0, image: "2ndmask.jpg" },
  { id: 3, title: "Beaded Jewelry", category: "Jewelry", price: 3500.0, image: "jew.jpg" },
  { id: 4, title: "Clay Pottery", category: "Pottery", price: 500.0, image: "hand.jpg" }
];

let cart = JSON.parse(localStorage.getItem('tribalCart')) || [];

const cartDrawer = document.getElementById("cartDrawer");
const cartBtn = document.getElementById("cartBtn");
const closeCart = document.getElementById("closeCart");
const cartItemsContainer = document.getElementById("cartItems");
const cartCount = document.getElementById("cartCount");
const cartTotal = document.getElementById("cartTotal");
const clearCartBtn = document.getElementById("clearCart");
const checkoutBtn = document.getElementById("checkout");

if (cartBtn) {
  cartBtn.addEventListener("click", () => {
    cartDrawer.classList.add("open");
  });
}

if (closeCart) {
  closeCart.addEventListener("click", () => {
    cartDrawer.classList.remove("open");
  });
}

function addToCart(productId) {
  const product = products.find(p => p.id === productId);
  if (!product) return;

  const existing = cart.find(item => item.id === productId);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1 });
  }
  updateCart();
  showToast(`${product.title} added to cart! 🌿`);
}

function updateQuantity(productId, delta) {
  const item = cart.find(item => item.id === productId);
  if (item) {
    if (delta === 0) {
      cart = cart.filter(i => i.id !== productId);
    } else {
      item.qty += delta;
      if (item.qty <= 0) cart = cart.filter(i => i.id !== productId);
    }
    updateCart();
  }
}

if (clearCartBtn) {
  clearCartBtn.addEventListener("click", () => {
    cart = [];
    updateCart();
    showToast("Cart cleared! 🛒");
  });
}

if (checkoutBtn) {
  checkoutBtn.addEventListener("click", () => {
    if (cart.length === 0) {
      showToast("Your cart is empty!");
    } else {
      showToast("Redirecting to checkout...");
      setTimeout(() => {
        alert(`Proceeding to payment for ₹${cartTotal.textContent}. Thank you for empowering artisans!`);
        cart = [];
        updateCart();
        cartDrawer.classList.remove("open");
      }, 1000);
    }
  });
}

function updateCart() {
  localStorage.setItem('tribalCart', JSON.stringify(cart));
  cartItemsContainer.innerHTML = "";
  let total = 0;

  cart.forEach(item => {
    const div = document.createElement("div");
    div.className = "cart-item";
    div.innerHTML = `
      <img src="${item.image}" alt="${item.title}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 12px;" />
      <div style="flex: 1; margin-left: 12px;">
        <strong>${item.title}</strong><br />
        ₹${item.price.toFixed(2)} x 
        <button onclick="updateQuantity(${item.id}, -1)">-</button>
        ${item.qty}
        <button onclick="updateQuantity(${item.id}, 1)">+</button>
      </div>
      <button onclick="updateQuantity(${item.id}, 0)">Remove</button>
    `;
    cartItemsContainer.appendChild(div);
    total += item.price * item.qty;
  });

  if (cart.length === 0) {
    cartItemsContainer.innerHTML = '<p style="text-align: center; color: #7D5A50;">Your cart is empty</p>';
  }

  if (cartCount) cartCount.textContent = cart.reduce((acc, item) => acc + item.qty, 0);
  if (cartTotal) cartTotal.textContent = total.toFixed(2);
}

// Products Grid
const productsGrid = document.getElementById("productsGrid");
function displayProducts(list) {
  productsGrid.innerHTML = "";
  list.forEach(product => {
    const card = document.createElement("div");
    card.className = "card-prod";
    card.innerHTML = `
      <div class="prod-media"><img src="${product.image}" alt="${product.title}" loading="lazy"></div>
      <div class="card-body">
        <div class="prod-title">${product.title}</div>
        <div class="prod-meta">${product.category}</div>
        <div class="price">₹${product.price.toFixed(2)}</div>
        <button class="add-btn btn primary" onclick="addToCart(${product.id})">Add to Cart</button>
      </div>
    `;
    productsGrid.appendChild(card);
  });
}

// Search
const headerSearch = document.getElementById("headerSearch");
const searchBtn = document.getElementById("searchBtn");
function performSearch(query) {
  const filtered = products.filter(p =>
    p.title.toLowerCase().includes(query.toLowerCase()) ||
    p.category.toLowerCase().includes(query.toLowerCase())
  );
  displayProducts(filtered);
}

if (headerSearch) {
  headerSearch.addEventListener("input", e => performSearch(e.target.value));
}
if (searchBtn) {
  searchBtn.addEventListener("click", () => performSearch(headerSearch.value));
}

// Toast
const toast = document.getElementById("toast");
function showToast(msg) {
  if (toast) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3000);
  }
}

// Hero Buttons
const shopNowBtn = document.getElementById("shopNow");
const ourStoryBtn = document.getElementById("ourStory");

if (shopNowBtn) {
  shopNowBtn.addEventListener("click", () => {
    window.location.href = "shop.html";
  });
}

if (ourStoryBtn) {
  ourStoryBtn.addEventListener("click", () => {
    const modal = document.createElement("div");
    modal.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:100;padding:20px;";
    modal.innerHTML = `
      <div style="background:#fff;padding:2em;border-radius:20px;max-width:600px;text-align:center;position:relative;">
        <button onclick="this.parentElement.parentElement.remove()" style="position:absolute;top:10px;right:10px;background:transparent;border:none;font-size:20px;cursor:pointer;">✕</button>
        <h3>Our Story</h3>
        <p>TribalArt celebrates indigenous artisans, especially women, weaving traditions and empowerment into every piece. Explore their stories!</p>
      </div>
    `;
    document.body.appendChild(modal);
  });
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
  updateCart();
  if (productsGrid) displayProducts(products);
});
