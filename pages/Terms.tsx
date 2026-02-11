import React from 'react';

export const Terms: React.FC = () => {
  React.useEffect(() => {
    document.title = 'Terms of Service (Texas, USA) | ZuzuMood';
  }, []);

  return (
    <div className="pt-44 pb-20 bg-white min-h-screen">
      <div className="container mx-auto px-6 max-w-4xl">
        <p className="text-[10px] uppercase tracking-[0.35em] text-muted mb-4">Legal • Texas, United States</p>
        <h1 className="text-4xl md:text-5xl font-serif mb-8">Terms of Service</h1>
        <div className="space-y-6 text-sm leading-7 text-gray-700">
          <p>ZuzuMood operates from Texas, USA. By using this website, you agree to these terms and all applicable U.S. and Texas laws.</p>
          <p>Product purchases are completed on our official Etsy store. Pricing, shipping, returns, and payment processing are governed by Etsy and our Etsy shop policies.</p>
          <p>All website content, branding, and original design assets are protected intellectual property and may not be copied or redistributed without written permission.</p>
          <p>For legal notices or policy questions, use our Etsy contact channel at https://www.etsy.com/shop/ZuzuMood.</p>
        </div>
      </div>
    </div>
  );
};
