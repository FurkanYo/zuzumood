import React, { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { PRODUCTS, CATEGORIES } from '../services/data';
import { ProductCard } from '../components/ProductCard';

const normalizeCategoryParam = (value: string | null) => {
  if (!value) {
    return 'all';
  }

  const normalized = value
    .toLowerCase()
    .trim()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-');

  if (normalized === 'all' || normalized === 'all-products') {
    return 'all';
  }

  const matchById = CATEGORIES.find((category) => category.id === normalized);
  if (matchById) {
    return matchById.id;
  }

  const matchByName = CATEGORIES.find((category) => {
    const normalizedName = category.name
      .toLowerCase()
      .replace(/&/g, 'and')
      .replace(/[^a-z0-9]+/g, '-');
    return normalizedName === normalized;
  });

  return matchByName?.id ?? 'all';
};

export const Shop: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentCategory = normalizeCategoryParam(searchParams.get('cat'));
  const searchQuery = searchParams.get('q') || '';

  const filteredProducts = useMemo(() => {
    let result = PRODUCTS;

    if (currentCategory !== 'all') {
      result = result.filter((product) => product.category === currentCategory);
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter((product) =>
        product.title.toLowerCase().includes(q) ||
        product.description.toLowerCase().includes(q) ||
        product.category.toLowerCase().includes(q) ||
        product.details.some((detail) => detail.toLowerCase().includes(q))
      );
    }

    return result;
  }, [currentCategory, searchQuery]);

  const activeCategoryName = CATEGORIES.find(c => c.id === currentCategory)?.name || 'All Products';

  return (
    <div className="pt-48 pb-32 bg-white min-h-screen">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="max-w-2xl mb-24 animate-fade-in">
          <h1 className="text-5xl md:text-6xl font-serif uppercase tracking-widest mb-6">
            {searchQuery ? `Searching: ${searchQuery}` : activeCategoryName}
          </h1>
          <p className="text-xs text-muted uppercase tracking-[0.3em] leading-relaxed max-w-lg">
            {searchQuery 
              ? `Results from the ZuzuMood collective archive matching your search.`
              : (CATEGORIES.find(c => c.id === currentCategory)?.description || 'Exploring the intersection of mood and materiality through curated silhouettes.')
            }
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-8 border-b border-gray-100 pb-8 mb-16 overflow-x-auto no-scrollbar">
          <button 
            onClick={() => setSearchParams({ cat: 'all' })}
            className={`text-[9px] font-bold uppercase tracking-[0.4em] whitespace-nowrap transition-all ${currentCategory === 'all' && !searchQuery ? 'text-black border-b border-black pb-1' : 'text-muted hover:text-black'}`}
          >
            All Pieces
          </button>
          {CATEGORIES.map(cat => (
            <button 
              key={cat.id}
              onClick={() => setSearchParams({ cat: cat.id })}
              className={`text-[9px] font-bold uppercase tracking-[0.4em] whitespace-nowrap transition-all ${currentCategory === cat.id ? 'text-black border-b border-black pb-1' : 'text-muted hover:text-black'}`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Results Info */}
        <div className="flex justify-between items-center mb-12">
          <div className="flex items-center space-x-4">
            <span className="text-[9px] font-bold uppercase tracking-widest text-muted">{filteredProducts.length} Results</span>
            {searchQuery && (
              <button onClick={() => setSearchParams({ cat: 'all' })} className="text-[8px] uppercase tracking-widest underline opacity-50 hover:opacity-100">Clear Search</button>
            )}
          </div>
          <div className="flex space-x-6 text-[9px] font-bold uppercase tracking-widest">
            <button className="hover:text-black transition-colors">Sort: Newest First</button>
          </div>
        </div>

        {/* Product Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-20">
          {filteredProducts.map(p => <ProductCard key={p.id} product={p} />)}
        </div>

        {filteredProducts.length === 0 && (
          <div className="py-60 text-center">
            <p className="text-muted uppercase tracking-widest text-[10px] mb-8">No matching products were found for this search.</p>
            <button 
              onClick={() => setSearchParams({ cat: 'all' })}
              className="px-8 py-3 border border-black text-[9px] font-bold uppercase tracking-widest hover:bg-black hover:text-white transition-all"
            >
              Back to All Products
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
