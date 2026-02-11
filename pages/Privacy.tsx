import React from 'react';

export const Privacy: React.FC = () => {
  React.useEffect(() => {
    document.title = 'Privacy Policy (Texas, USA) | ZuzuMood';
  }, []);

  return (
    <div className="pt-44 pb-20 bg-white min-h-screen">
      <div className="container mx-auto px-6 max-w-4xl">
        <p className="text-[10px] uppercase tracking-[0.35em] text-muted mb-4">Legal • Texas, United States</p>
        <h1 className="text-4xl md:text-5xl font-serif mb-8">Privacy Policy</h1>
        <div className="space-y-6 text-sm leading-7 text-gray-700">
          <p>This website collects limited technical data such as browser information, page views, and basic analytics signals to improve performance and shopping flow.</p>
          <p>Orders and payment data are handled by Etsy when you continue to checkout on our official Etsy store.</p>
          <p>We do not sell personal data. Data handling follows applicable U.S. and Texas privacy standards for online businesses.</p>
          <p>If you need data or privacy support, contact us through our Etsy shop at https://www.etsy.com/shop/ZuzuMood.</p>
        </div>
      </div>
    </div>
  );
};
