
import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white pt-32 pb-12 border-t border-gray-50">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-16 mb-24">
          <div className="col-span-1">
            <h3 className="text-2xl font-serif tracking-[0.1em] mb-8 uppercase">ZuzuMood</h3>
            <p className="text-[10px] text-muted leading-relaxed uppercase tracking-widest max-w-xs">
              Based in Texas, USA. <br/><br/>
              A curated Soul Archive of original designs created in-house by our team. All orders are securely fulfilled via our official Etsy presence.
            </p>
          </div>
          
          <div>
            <h4 className="text-[10px] font-bold uppercase tracking-[0.4em] mb-8">The Archive</h4>
            <ul className="space-y-4 text-[10px] text-muted uppercase tracking-[0.2em]">
              <li className="hover:text-black transition-colors cursor-pointer underline-offset-4 hover:underline">Explore All Pieces</li>
              <li><a href="https://www.etsy.com/shop/ZuzuMood" target="_blank" rel="noreferrer" className="hover:text-black transition-colors underline-offset-4 hover:underline">Official Etsy Store</a></li>
              <li className="hover:text-black transition-colors cursor-pointer underline-offset-4 hover:underline">Original Designs</li>
            </ul>
          </div>

          <div>
            <h4 className="text-[10px] font-bold uppercase tracking-[0.4em] mb-8">Customer Care</h4>
            <ul className="space-y-4 text-[10px] text-muted uppercase tracking-[0.2em]">
              <li><a href="https://www.etsy.com/shop/ZuzuMood#policies" target="_blank" rel="noreferrer" className="hover:text-black transition-colors underline-offset-4 hover:underline">Shipping (USA & Global)</a></li>
              <li><a href="https://www.etsy.com/shop/ZuzuMood#policies" target="_blank" rel="noreferrer" className="hover:text-black transition-colors underline-offset-4 hover:underline">Return Policy</a></li>
              <li className="hover:text-black transition-colors cursor-pointer underline-offset-4 hover:underline">Size Guide</li>
            </ul>
          </div>

          <div>
            <h4 className="text-[10px] font-bold uppercase tracking-[0.4em] mb-8">Connect</h4>
            <div className="flex flex-col space-y-4 text-[10px] text-muted uppercase tracking-[0.2em]">
              <span className="hover:text-black transition-colors cursor-pointer">Instagram</span>
              <span className="hover:text-black transition-colors cursor-pointer">Pinterest</span>
              <form className="mt-4">
                <input 
                  type="email" 
                  placeholder="Texas Studio Newsletter" 
                  className="bg-transparent border-b border-gray-300 py-2 w-full text-[9px] focus:border-black outline-none transition-colors uppercase tracking-widest"
                />
              </form>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center text-[8px] font-bold uppercase tracking-[0.5em] text-muted">
          <span>© 2025 ZuzuMood Studio • Proudly Based in Texas • Fulfilled by Etsy.</span>
          <div className="mt-4 md:mt-0 flex space-x-8">
            <span>Terms of Service</span>
            <span>Privacy Archive</span>
            <span className="text-black">English (US)</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
