export interface Product {
  id: string;
  title: string;
  price: number;
  originalPrice?: number;
  category: 'valentines' | 'aesthetic' | 'healing' | 'music' | 'teacher' | 'patriotic' | 'bridal' | 'family';
  image: string;
  images: string[];
  isNew?: boolean;
  isOnSale?: boolean;
  description: string;
  details: string[];
  etsyUrl?: string;
}

export interface Category {
  id: string;
  name: string;
  description: string;
}

export interface CartItem extends Product {
  selectedSize: string;
  quantity: number;
}
