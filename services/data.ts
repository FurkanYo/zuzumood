import { Product, Category } from '../types';
import etsyListingsCsv from '../products/EtsyListingsDownload.csv?raw';

const CATEGORY_DEFINITIONS: Record<Product['category'], Omit<Category, 'id'>> = {
  valentines: {
    name: 'Valentines',
    description: 'Gifts for bold spirits and soulmate connections. Handcrafted for the modern romantic.'
  },
  aesthetic: {
    name: 'Aesthetic',
    description: 'Quiet luxury and minimalist silhouettes using premium Comfort Colors and Gildan fabrics.'
  },
  healing: {
    name: 'Healing & Stoic',
    description: 'Wearable reminders to pause, reflect, and reconnect with your inner strength.'
  },
  music: {
    name: 'Rock & Vinyl',
    description: 'Inspired by the rhythms of the 70s and the soul of analog sound.'
  },
  teacher: {
    name: 'Teacher',
    description: 'Academic sophistication for the modern educator. Personalized and premium.'
  },
  patriotic: {
    name: 'Liberty & Truth',
    description: 'Statement pieces for those who believe in freedom, transparency, and independence.'
  },
  bridal: {
    name: 'Bridal Atelier',
    description: 'Celebratory pieces for your wedding morning, bachelorette, and honeymoon era.'
  },
  family: {
    name: 'Legacy & Kin',
    description: 'Celebrating the miracle of new beginnings and the strength of family bonds.'
  }
};

const CATEGORY_RULES: Array<{ category: Product['category']; keywords: string[] }> = [
  { category: 'bridal', keywords: ['bride', 'bridal', 'wedding', 'bachelorette', 'honeymoon', 'mrs'] },
  { category: 'teacher', keywords: ['teacher', 'professor', 'school', 'educator', 'back_to_school', 'faculty'] },
  { category: 'healing', keywords: ['faith', 'christian', 'bible', 'healing', 'jesus', 'prayer', 'stoic'] },
  { category: 'music', keywords: ['vinyl', 'rock', 'band', 'music', 'album', 'cassette'] },
  { category: 'patriotic', keywords: ['america', 'usa', 'patriot', 'freedom', 'politic', 'liberty', 'ice'] },
  { category: 'family', keywords: ['mom', 'mama', 'dad', 'family', 'baby', 'pregnancy', 'couple', 'anniversary'] },
  { category: 'valentines', keywords: ['valentine', 'lover', 'romantic', 'soulmate', 'heart'] }
];

const parseCsv = (csv: string): string[][] => {
  const rows: string[][] = [];
  let row: string[] = [];
  let value = '';
  let isInQuotes = false;

  const flushValue = () => {
    row.push(value);
    value = '';
  };

  const flushRow = () => {
    rows.push(row);
    row = [];
  };

  for (let i = 0; i < csv.length; i += 1) {
    const char = csv[i];
    const nextChar = csv[i + 1];

    if (char === '"') {
      if (isInQuotes && nextChar === '"') {
        value += '"';
        i += 1;
      } else {
        isInQuotes = !isInQuotes;
      }
      continue;
    }

    if (!isInQuotes && char === ',') {
      flushValue();
      continue;
    }

    if (!isInQuotes && (char === '\n' || char === '\r')) {
      if (char === '\r' && nextChar === '\n') {
        i += 1;
      }
      flushValue();
      flushRow();
      continue;
    }

    value += char;
  }

  if (value.length > 0 || row.length > 0) {
    flushValue();
    flushRow();
  }

  return rows.filter((csvRow) => csvRow.some((cell) => cell.trim().length > 0));
};

const normalizeForSearch = (value: string) => value.toLowerCase().replace(/\s+/g, ' ').trim();

const toSlug = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);

const getCategory = (title: string, tags: string): Product['category'] => {
  const haystack = `${normalizeForSearch(title)} ${normalizeForSearch(tags)}`;

  const match = CATEGORY_RULES.find((rule) =>
    rule.keywords.some((keyword) => haystack.includes(keyword.toLowerCase()))
  );

  return match?.category ?? 'aesthetic';
};

const getEtsyLink = (title: string) =>
  `https://www.etsy.com/shop/ZuzuMood?search_query=${encodeURIComponent(title)}`;

const csvRows = parseCsv(etsyListingsCsv);
const header = csvRows[0] ?? [];
const dataRows = csvRows.slice(1);

const indexOf = (columnName: string) => header.indexOf(columnName);

const getCell = (cells: string[], columnName: string) => {
  const columnIndex = indexOf(columnName);
  return columnIndex >= 0 ? (cells[columnIndex] ?? '').trim() : '';
};

export const PRODUCTS: Product[] = dataRows
  .map((cells, rowIndex) => {
    const title = getCell(cells, 'TITLE');
    const description = getCell(cells, 'DESCRIPTION');
    const price = Number.parseFloat(getCell(cells, 'PRICE'));
    const image = getCell(cells, 'IMAGE1');
    const sku = getCell(cells, 'SKU');
    const tags = getCell(cells, 'TAGS');
    const materials = getCell(cells, 'MATERIALS');

    if (!title || !image || Number.isNaN(price)) {
      return null;
    }

    const details = [
      ...materials
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      ...tags
        .split(',')
        .map((item) => item.replace(/_/g, ' ').trim())
        .filter(Boolean)
        .slice(0, 4)
    ];

    const idBase = sku.toLowerCase().replace(/[^a-z0-9]+/g, '-') || toSlug(title) || `product-${rowIndex + 1}`;

    return {
      id: idBase,
      title,
      price,
      category: getCategory(title, tags),
      image,
      description,
      details: details.length > 0 ? details : ['Etsy exclusive design'],
      isNew: rowIndex < 8,
      etsyUrl: getEtsyLink(title)
    } as Product;
  })
  .filter((product): product is Product => Boolean(product));

export const CATEGORIES: Category[] = Object.entries(CATEGORY_DEFINITIONS)
  .map(([id, config]) => ({
    id,
    ...config
  }))
  .filter((category) => PRODUCTS.some((product) => product.category === category.id));
