import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# Thiết lập hệ thống ghi log
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ProductMetrics(BaseModel):
    """Khuôn mẫu dữ liệu sản phẩm chuẩn hóa (dùng Pydantic để validate)"""
    product_id: str
    title: str
    price: float = Field(gt=0, description="Giá sản phẩm phải lớn hơn 0")
    sales_count_30d: int = Field(ge=0, description="Lượt bán trong 30 ngày")
    rating: float = Field(ge=0, le=5, description="Điểm đánh giá từ 0 đến 5 sao")
    commission_rate: float = Field(ge=0, le=100, description="Tỷ lệ hoa hồng (%)")
    is_official_shop: bool = False
    product_url: str

class ProductAnalyzer:
    """Module phân tích & sàng lọc sản phẩm Winner cho Affiliate"""
    
    def __init__(self, min_rating: float = 4.5, min_sales: int = 50):
        self.min_rating = min_rating
        self.min_sales = min_sales

    def calculate_winner_score(self, product: ProductMetrics) -> float:
        """Thuật toán tính Điểm Sản Phẩm Winner (Thang điểm 100)"""
        # 1. Điểm đánh giá (Tối đa 30 điểm)
        rating_score = (product.rating / 5.0) * 30
        
        # 2. Điểm lượt bán (Tối đa 30 điểm - Giới hạn mốc 1000 đơn)
        sales_score = min(product.sales_count_30d / 1000.0, 1.0) * 30
        
        # 3. Điểm hoa hồng (Tối đa 30 điểm - Giới hạn mốc 20% hoa hồng)
        commission_score = min(product.commission_rate / 20.0, 1.0) * 30
        
        # 4. Điểm uy tín Shop Mall/Chính hãng (Tối đa 10 điểm)
        trust_score = 10.0 if product.is_official_shop else 5.0
        
        total_score = rating_score + sales_score + commission_score + trust_score
        return round(total_score, 2)

    def filter_winner_products(self, raw_products: List[Dict]) -> List[Dict]:
        """Lọc và sắp xếp các sản phẩm ngon nhất từ danh sách thô"""
        winning_list = []
        
        for item in raw_products:
            try:
                # Validate dữ liệu đầu vào
                product = ProductMetrics(**item)
                
                # Điều kiện lọc tối thiểu
                if product.rating < self.min_rating or product.sales_count_30d < self.min_sales:
                    continue
                    
                score = self.calculate_winner_score(product)
                
                product_data = product.model_dump()
                product_data["winner_score"] = score
                winning_list.append(product_data)
                
            except Exception as e:
                logging.warning(f"Bỏ qua sản phẩm lỗi dữ liệu {item.get('product_id', 'Unknown')}: {e}")
                continue

        # Sắp xếp theo điểm Winner giảm dần
        winning_list.sort(key=lambda x: x["winner_score"], reverse=True)
        logging.info(f"Đã phân tích {len(raw_products)} sản phẩm. Tìm thấy {len(winning_list)} sản phẩm đạt chuẩn Winner.")
        return winning_list

# Test nhanh module khi chạy trực tiếp
if __name__ == "__main__":
    mock_data = [
        {
            "product_id": "SP001",
            "title": "Tai nghe Bluetooth Không Dây Pin Trâu",
            "price": 250000,
            "sales_count_30d": 1200,
            "rating": 4.8,
            "commission_rate": 15.0,
            "is_official_shop": True,
            "product_url": "https://shopee.vn/product-sample-1"
        },
        {
            "product_id": "SP002",
            "title": "Áo Thun Nam Giá Rẻ",
            "price": 49000,
            "sales_count_30d": 15,
            "rating": 3.9,  # Sẽ bị loại do rating < 4.5
            "commission_rate": 5.0,
            "is_official_shop": False,
            "product_url": "https://shopee.vn/product-sample-2"
        }
    ]
    
    analyzer = ProductAnalyzer()
    results = analyzer.filter_winner_products(mock_data)
    print("\n--- KẾT QUẢ SĂN SẢN PHẨM WINNER ---")
    for p in results:
        print(f"[{p['winner_score']} Điểm] {p['title']} - Giá: {p['price']:,}đ - Hoa hồng: {p['commission_rate']}%")