ALTER TABLE customers 
ADD CONSTRAINT unique_customer UNIQUE(name, class, level);

ALTER TABLE cart_items 
ADD CONSTRAINT unique_cart_item UNIQUE(cart_id, item_sku);