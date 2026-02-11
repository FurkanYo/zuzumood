import { Product, Category } from '../types';

export const CATEGORIES: Category[] = [
  { id: 'valentines', name: 'Valentines', description: 'Gifts for bold spirits and soulmate connections. Handcrafted for the modern romantic.' },
  { id: 'aesthetic', name: 'Aesthetic Archive', description: 'Quiet luxury and minimalist silhouettes using premium Comfort Colors and Gildan fabrics.' },
  { id: 'healing', name: 'Healing & Stoic', description: 'Wearable reminders to pause, reflect, and reconnect with your inner strength.' },
  { id: 'music', name: 'Rock & Vinyl', description: 'Inspired by the rhythms of the 70s and the soul of analog sound.' },
  { id: 'teacher', name: 'Teacher Edit', description: 'Academic sophistication for the modern educator. Personalized and premium.' },
  { id: 'patriotic', name: 'Liberty & Truth', description: 'Statement pieces for those who believe in freedom, transparency, and independence.' },
  { id: 'bridal', name: 'Bridal Atelier', description: 'Celebratory pieces for your wedding morning, bachelorette, and honeymoon era.' },
  { id: 'family', name: 'Legacy & Kin', description: 'Celebrating the miracle of new beginnings and the strength of family bonds.' },
];

const getEtsyLink = (title: string) => `https://www.etsy.com/shop/ZuzuMood?search_query=${encodeURIComponent(title)}`;

export const PRODUCTS: Product[] = [
  // FEATURED & NEW (Non-CSV rounded out items)
  {
    id: 'zm-000',
    title: 'Signature Maison Oversized Blank',
    price: 32.00,
    category: 'aesthetic',
    image: 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?q=80&w=1000',
    description: 'The foundation of the Soul Archive. A premium, heavyweight 100% cotton blank for those who speak in silence.',
    details: ['100% Ring-Spun Cotton', 'Double-needle stitching', 'Pre-shrunk', 'Minimalist fit'],
    isNew: true,
    etsyUrl: 'https://www.etsy.com/shop/ZuzuMood'
  },
  // CSV ITEMS REFINED FOR SEO
  {
    id: 'zm-172',
    title: 'Faith-Filled Minimalist Christian Bridal Sweatshirt',
    price: 30.00,
    category: 'bridal',
    image: 'https://i.etsystatic.com/63666514/r/il/dc4aeb/7745338633/il_fullxfull.7745338633_c953.jpg',
    description: 'Timeless Christian bridal sweatshirt for wedding mornings and bridal showers. Minimal script with a delicate veil detail.',
    details: ['Gildan 18000 Heavyweight', 'Unisex Relaxed Fit', 'Bridal Keepsake', 'Designed in the USA inspired aesthetic'],
    etsyUrl: getEtsyLink('Faith Filled Bride Sweatshirt')
  },
  {
    id: 'zm-171',
    title: 'Faith Over Fear Minimalist Christian Hoodie',
    price: 39.99,
    category: 'healing',
    image: 'https://i.etsystatic.com/63666514/r/il/b54a7a/7744562467/il_fullxfull.7744562467_s4db.jpg',
    description: 'A daily reminder of spiritual strength. "Faith Over Fear" in a clean, modern layout for daily confidence.',
    details: ['Premium Fleece Lined', 'Unisex Comfort Fit', 'High-Definition DTG Print', 'Minimalist Religious Quote'],
    etsyUrl: getEtsyLink('Faith Over Fear Hoodie')
  },
  {
    id: 'zm-169',
    title: 'Comfort Colors 1717 Personalized Professor Sweatshirt',
    price: 19.99,
    category: 'teacher',
    image: 'https://i.etsystatic.com/63666514/r/il/7263af/7689926358/il_fullxfull.7689926358_jzt4.jpg',
    description: 'Academic sophistication using the legendary Comfort Colors 1717 garment-dyed fabric. Personalized for the modern educator.',
    details: ['100% Ring-Spun Cotton', 'Garment-Dyed Vintage Look', 'Sanchez Font Typography', 'Personalized Teacher Gift'],
    etsyUrl: getEtsyLink('Personalized Teacher Sweatshirt')
  },
  {
    id: 'zm-168',
    title: 'Custom Minimalist Apple Teacher Appreciation Sweatshirt',
    price: 30.00,
    category: 'teacher',
    image: 'https://i.etsystatic.com/63666514/r/il/a50d61/7689485596/il_fullxfull.7689485596_870q.jpg',
    description: 'Celebrate your favorite educator with our minimalist apple design. Features a custom name integrated with modern elegance.',
    details: ['Gildan 18000 Series', 'Teacher Appreciation Gift', 'School Year Essential', 'Premium Soft Texture'],
    etsyUrl: getEtsyLink('Custom Teacher Shirt')
  },
  {
    id: 'zm-167',
    title: 'Vintage 1976 Birthday Milestone Comfort Colors Tee',
    price: 19.99,
    category: 'aesthetic',
    image: 'https://i.etsystatic.com/63666514/r/il/80f003/7731595355/il_fullxfull.7731595355_osij.jpg',
    description: 'Capture the legend of 1976. Authentic retro vibe with a professionally distressed, sun-faded graphic.',
    details: ['Garment-Dyed Fabric', '70s Palette Inspired', 'Relaxed Unisex Fit', 'Vintage Milestone Quality'],
    etsyUrl: getEtsyLink('Vintage 1976 Birthday Shirt')
  },
  {
    id: 'zm-166',
    title: 'Jesus John 14:6 Leopard Print Christian Sweatshirt',
    price: 30.00,
    category: 'healing',
    image: 'https://i.etsystatic.com/63666514/r/il/632ecb/7730597615/il_fullxfull.7730597615_qfd9.jpg',
    description: 'Wear your faith with a modern touch. Trendy cheetah print varsity letters featuring the powerful John 14:6 message.',
    details: ['Soft Cotton/Poly Blend', 'Scripture Based Art', 'Trendy Animal Print', 'Aesthetic Faith Wear'],
    etsyUrl: getEtsyLink('Christian Sweatshirt John 14:6')
  },
  {
    id: 'zm-165',
    title: 'Political Humor Statement Sweatshirt - He Is On The List',
    price: 30.00,
    category: 'patriotic',
    image: 'https://i.etsystatic.com/63666514/r/il/71c10f/7728507089/il_fullxfull.7728507089_loaz.jpg',
    description: 'A provocative conversation starter. Minimalist typography with hidden landscape art for those who stay informed.',
    details: ['High-Definition Print', 'Sarcastic Political Art', 'Heavyweight Comfort', 'Limited Edition Satire'],
    etsyUrl: getEtsyLink('Political Humor Shirt')
  },
  {
    id: 'zm-160',
    title: 'Abolish ICE Human Rights Activist Hoodie',
    price: 30.00,
    category: 'patriotic',
    image: 'https://i.etsystatic.com/63666514/r/il/fadea1/7675545522/il_fullxfull.7675545522_be4f.jpg',
    description: 'Stand for justice. Hand-drawn illustration capturing the fragility of safety and the cry for humanitarian empathy.',
    details: ['Activist Design', 'Political Social Justice', 'Durable Print Quality', 'Meaningful Gift for Change'],
    etsyUrl: getEtsyLink('Seals Against ICE')
  },
  {
    id: 'zm-158',
    title: 'Dark Academia Book Lover Librarian Sweatshirt',
    price: 30.00,
    category: 'aesthetic',
    image: 'https://i.etsystatic.com/63666514/r/il/fbdce0/7675040048/il_fullxfull.7675040048_2pwr.jpg',
    description: 'Designed for the bibliophile soul. Minimalist aesthetic for teachers, students, and librarians who live in chapters.',
    details: ['Medium-Heavy Fabric', 'Bookish Quote Style', 'Intellectual Aesthetic', 'Cozy Reading Jumper'],
    etsyUrl: getEtsyLink('Book Lover Sweatshirt')
  },
  {
    id: 'zm-111',
    title: 'Capybara Ballerina Quirky Aesthetic Comfort Colors Tee',
    price: 19.99,
    category: 'aesthetic',
    image: 'https://i.etsystatic.com/63666514/r/il/d2ef39/7667623415/il_fullxfull.7667623415_gd86.jpg',
    description: 'Chill meets elegance. A whimsical capybara on tiptoes in ballet shoes. Quirky humor for animal lovers.',
    details: ['100% Ring-Spun Cotton', 'Quirky Animal Humor', 'Balletcore Aesthetic', 'Vintage Lived-in Feel'],
    etsyUrl: getEtsyLink('Capybara Ballerina')
  },
  {
    id: 'zm-92',
    title: 'A Lot Going On At The Moment Red Glitter Concert Tee',
    price: 19.99,
    category: 'music',
    image: 'https://i.etsystatic.com/63666514/r/il/1f94c8/7656337273/il_fullxfull.7656337273_5sa6.jpg',
    description: 'Shine in Comfort Colors. Featuring a custom red glitter star inside the "A". The ultimate concert essential.',
    details: ['Premium Textured Glitter', 'Swiftie Fan Inspired', 'Heavyweight Relaxed Fit', 'Double-Needle Stitching'],
    etsyUrl: getEtsyLink('A Lot Going On At The Moment Glitter Tee')
  },
  {
    id: 'zm-86',
    title: 'Cherry Blossom Family Bond Minimalist Line Art Hoodie',
    price: 45.00,
    category: 'family',
    image: 'https://i.etsystatic.com/63666514/r/il/2a4d76/7597347452/il_fullxfull.7597347452_6e7r.jpg',
    description: 'Poetic grace for the modern family. Delicate line art fused with blooming cherry blossoms capturing togetherness.',
    details: ['Quiet Luxury Style', 'Family Legacy Art', 'Premium Soft-Touch', 'Floral Motherhood Gift'],
    etsyUrl: getEtsyLink('Embroidered Mother Child Hoodie')
  }
];