import React, { useState, useRef, useEffect } from 'react';
import { GoogleGenAI, Type } from '@google/genai';
import { Sparkles, X, MessageSquare, Send, Loader2 } from 'lucide-react';
import { PRODUCTS } from '../services/data';
import { Link } from 'react-router-dom';

export const AIStylist: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'model'; text: string }[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, loading]);

  const handleConsult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg = query;
    setQuery('');
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const geminiApiKey = __GEMINI_API_KEY__ || import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.GEMINI_API_KEY || import.meta.env.GEMINI_KEY || import.meta.env.API_KEY;

      if (!geminiApiKey) {
        throw new Error('Missing Gemini API key. Add VITE_GEMINI_API_KEY (recommended) or GEMINI_API_KEY in your deploy env.');
      }

      // Create a new instance right before making an API call to ensure it uses the latest configured key.
      const ai = new GoogleGenAI({ apiKey: geminiApiKey });
      
      const systemInstruction = `
        You are the ZuzuMood AI Stylist. ZuzuMood is a high-end minimalist apparel studio.
        
        BRAND FACTS:
        - We are based in Texas, USA.
        - Website: zuzumood.com (This is our official lookbook).
        - Sales: We sell EXCLUSIVELY on Etsy. Never suggest buying directly on our website.
        - Production: Every single design is created 100% in-house by our Texas design team. We are not resellers.
        - Materials: We primarily use premium Comfort Colors 1717 and heavyweight fleece.
        
        BEHAVIOR:
        - Tone: Sophisticated, Texas-warmth, minimalist, and honest.
        - Goal: Help users find the right "mood-wear" from our archive.
        - Constraint: Recommend only products from the list provided below.
        - Language: English only.
        
        PRODUCT ARCHIVE:
        ${JSON.stringify(PRODUCTS.map(p => ({ id: p.id, title: p.title, category: p.category, description: p.description })))}
        
        FORMAT: Respond in JSON format only.
      `;

      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `${systemInstruction}\n\nUser Question: ${userMsg}`,
        config: {
          responseMimeType: 'application/json',
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              message: { type: Type.STRING },
              recommendedProductIds: { 
                type: Type.ARRAY, 
                items: { type: Type.STRING } 
              }
            },
            required: ['message', 'recommendedProductIds']
          }
        }
      });

      // The simplest and most direct way to get the generated text content is by accessing the .text property.
      const data = JSON.parse(response.text || '{}');
      setChatHistory(prev => [...prev, { role: 'model', text: data.message }]);
      
      const suggested = PRODUCTS.filter(p => data.recommendedProductIds?.includes(p.id));
      setRecommendations(suggested);

    } catch (err) {
      console.error('AI Error:', err);
      setChatHistory(prev => [...prev, { role: 'model', text: "I'm sorry, our Texas studio is currently offline. Please reach out to us via Etsy or try again later." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-8 right-8 z-[100] bg-black text-white w-14 h-14 rounded-full flex items-center justify-center shadow-2xl hover:scale-110 active:scale-95 transition-all duration-300"
        aria-label="Open AI Stylist"
      >
        <Sparkles className="w-5 h-5" />
      </button>

      {/* Overlay */}
      <div 
        className={`fixed inset-0 bg-black/30 backdrop-blur-sm z-[110] transition-opacity duration-700 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} 
        onClick={() => setIsOpen(false)} 
      />

      {/* Panel */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-md bg-white z-[120] shadow-2xl transition-transform duration-700 ease-in-out transform ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-8 border-b border-gray-100 flex justify-between items-center bg-white">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-[0.4em]">The AI Stylist</h2>
              <p className="text-[9px] text-muted uppercase tracking-widest mt-1 italic">Texas Studio Support</p>
            </div>
            <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-gray-50 rounded-full transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Chat Container */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-8 space-y-8 no-scrollbar bg-white">
            {chatHistory.length === 0 && (
              <div className="text-center py-20 animate-fade-in">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-8">
                  <MessageSquare className="w-6 h-6 text-gray-300" />
                </div>
                <h3 className="text-[11px] font-bold uppercase tracking-widest mb-4">Maison ZuzuMood</h3>
                <p className="text-[10px] text-muted uppercase tracking-[0.2em] leading-relaxed max-w-[260px] mx-auto">
                  Based in Texas, our studio creates original designs for bold spirits. How can I guide your discovery today?
                </p>
              </div>
            )}
            
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[90%] p-5 text-[11px] tracking-[0.05em] leading-[1.8] ${
                  msg.role === 'user' 
                  ? 'bg-black text-white' 
                  : 'bg-gray-50 text-black border border-gray-100'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-50 p-5 border border-gray-100">
                  <Loader2 className="w-4 h-4 animate-spin text-black" />
                </div>
              </div>
            )}

            {recommendations.length > 0 && !loading && (
              <div className="grid grid-cols-2 gap-6 mt-12 pt-12 border-t border-gray-100 animate-fade-in">
                {recommendations.map(p => (
                  <Link key={p.id} to={`/product/${p.id}`} onClick={() => setIsOpen(false)} className="group block">
                    <div className="aspect-[3/4] overflow-hidden bg-gray-50 mb-3 relative">
                      <img src={p.image} className="w-full h-full object-cover grayscale-[20%] group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700" alt={p.title} />
                    </div>
                    <h3 className="text-[9px] font-bold uppercase tracking-widest truncate leading-relaxed">{p.title}</h3>
                    <p className="text-[8px] text-muted font-bold mt-1.5 uppercase tracking-widest">
                      ${p.price.toFixed(2)} • Etsy Exclusive
                    </p>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-8 border-t border-gray-100 bg-white">
            <form onSubmit={handleConsult} className="relative group">
              {/* Corrected the state setter to setQuery and removed duplicate input/scripts */}
              <input 
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask our Texas studio..."
                className="w-full border-b border-gray-200 py-4 text-[11px] focus:border-black outline-none uppercase tracking-widest transition-all placeholder:text-gray-300"
                autoComplete="off"
              />
              <button 
                type="submit" 
                disabled={loading || !query.trim()}
                className={`absolute right-0 top-1/2 -translate-y-1/2 p-2 transition-all ${
                  query.trim() ? 'text-black scale-110' : 'text-gray-200'
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <p className="mt-4 text-[7px] text-muted uppercase tracking-[0.3em] text-center">
              Texas Studio Original Designs • Secured by Etsy
            </p>
          </div>
        </div>
      </div>
    </>
  );
};