
import React from 'react';
import { Link } from 'react-router-dom';
import { PRODUCTS } from '../services/data';
import { ProductCard } from '../components/ProductCard';

export const Home: React.FC = () => {
  const featured = PRODUCTS.slice(0, 4);

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        <video 
          autoPlay 
          muted 
          loop 
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-90 grayscale-[20%]"
        >
          <source src="https://assets.mixkit.co/videos/preview/mixkit-fashion-model-walking-on-the-street-4395-large.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/40" />
        <div className="relative z-10 text-center px-6">
          <h2 className="text-[10px] font-bold tracking-[0.6em] uppercase mb-8 text-white/90 animate-fade-in">Texas Studio • Soul Archive</h2>
          <h1 className="text-6xl md:text-9xl font-serif text-white mb-12 leading-none tracking-tight">Bold Spirits<br/>Golden Radiance</h1>
          <Link to="/shop" className="inline-block border border-white text-white px-12 py-5 text-[10px] font-bold uppercase tracking-[0.4em] hover:bg-white hover:text-black transition-all duration-700 ease-in-out">
            Explore the Collection
          </Link>
        </div>
      </section>

      {/* Philosophy Section */}
      <section className="py-40 px-6">
        <div className="container mx-auto max-w-4xl text-center">
          <h3 className="text-[10px] font-bold uppercase tracking-[0.4em] mb-12 text-muted">The Texas-Based Mission</h3>
          <p className="text-2xl md:text-4xl font-serif italic leading-relaxed mb-12">
            "ZuzuMood is a curated 'Soul Archive' born in Texas. We design wearable reminders for bold spirits, ensuring every original design helps you pause, reflect, and reconnect."
          </p>
          <p className="text-base md:text-lg text-gray-700 mb-10">
            ZuzuMood&apos;un güzel ve anlamlı parçalar yaratma felsefesiyle mükemmel bir şekilde örtüşüyor.
          </p>
          <img
            src="/blog/ChatGPT%20Image%2013%20%C5%9Eub%202026%2000_02_21.png"
            alt="ZuzuMood brand philosophy visual"
            className="mx-auto w-full max-w-2xl rounded-sm mb-12"
            loading="lazy"
          />
          <div className="flex flex-col items-center">
            <span className="text-[9px] font-bold uppercase tracking-[0.3em] text-black mb-1">Zuleyha Akkan</span>
            <span className="text-[8px] text-muted uppercase tracking-widest italic">In-House Design Director • Texas, USA</span>
          </div>
        </div>
      </section>

      {/* Featured Grid */}
      <section className="py-24 px-6 border-t border-gray-50">
        <div className="container mx-auto">
          <div className="flex justify-between items-end mb-16">
            <div>
              <h2 className="text-4xl font-serif uppercase tracking-widest">Seasonal Archival</h2>
              <p className="text-[10px] text-muted uppercase tracking-[0.3em] mt-2">Original Studio Designs</p>
            </div>
            <Link to="/shop" className="text-[9px] font-bold uppercase tracking-[0.3em] border-b border-black pb-1">Shop Full Archive</Link>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
            {featured.map(p => <ProductCard key={p.id} product={p} />)}
          </div>
        </div>
      </section>

      {/* Wild Elegance Editorial */}
      <section className="py-40 grid grid-cols-1 md:grid-cols-2">
        <div className="h-[600px] md:h-[800px] relative group overflow-hidden">
          <img src="https://images.unsplash.com/photo-1544441893-675973e31985?q=80&w=1000" className="w-full h-full object-cover transition-transform duration-[2000ms] group-hover:scale-110" alt="Wild Elegance" />
          <div className="absolute inset-0 bg-black/30 flex flex-col justify-end p-12">
            <h4 className="text-3xl font-serif text-white mb-4 italic">Wild Elegance</h4>
            <p className="text-[10px] text-white/80 uppercase tracking-widest mb-8 max-w-xs">Featuring the original Gold Leopard Heart studio design.</p>
            <Link to="/shop?cat=aesthetic" className="text-[10px] font-bold uppercase tracking-[0.3em] text-white underline underline-offset-8 decoration-white/50 hover:decoration-white transition-all">Discover Original Designs</Link>
          </div>
        </div>
        <div className="h-[600px] md:h-[800px] relative group overflow-hidden bg-accent flex items-center justify-center p-20">
           <div className="text-center">
              <h4 className="text-sm font-bold uppercase tracking-[0.5em] mb-12">Bridal & Celebration</h4>
              <h3 className="text-5xl font-serif mb-12">Original Pieces for <br/>Soulmate Connections</h3>
              <Link to="/shop?cat=bridal" className="inline-block bg-black text-white px-10 py-4 text-[9px] font-bold uppercase tracking-[0.4em] hover:bg-muted transition-colors">Shop Bridal Atelier</Link>
           </div>
        </div>
      </section>

      {/* Daily Trend Blog */}
      <section className="py-24 px-6 border-t border-gray-50 bg-neutral-50">
        <div className="container mx-auto max-w-5xl text-center">
          <p className="text-[10px] uppercase tracking-[0.35em] text-muted mb-5">New Every Day • 10:00 AM Texas Research Cycle</p>
          <h3 className="text-4xl md:text-5xl font-serif mb-6">Daily US Fashion</h3>
          <p className="text-base md:text-lg text-gray-700 leading-relaxed max-w-3xl mx-auto mb-8">
            Access daily US fashion trend articles from one place.
          </p>
          <Link to="/blog" className="inline-block bg-black text-white px-10 py-4 text-[10px] font-bold uppercase tracking-[0.35em] hover:bg-muted transition-colors">
            Explore Blog
          </Link>
        </div>
      </section>
    </div>
  );
};
