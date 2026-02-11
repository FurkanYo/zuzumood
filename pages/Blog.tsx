import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

interface BlogPostMeta {
  slug: string;
  title: string;
  summary: string;
  date: string;
  path: string;
  image?: string;
}

interface MarkdownBlock {
  type: 'h1' | 'h2' | 'p' | 'hr';
  content?: string;
}

const BASE_URL = import.meta.env.BASE_URL || '/';

const toAssetUrl = (value: string): string => {
  if (!value) {
    return BASE_URL;
  }

  if (/^https?:\/\//.test(value)) {
    return value;
  }

  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL;
  const cleanPath = value.startsWith('/') ? value : `/${value}`;
  return `${cleanBase}${cleanPath}`;
};

const stripFrontmatter = (markdown: string): string => {
  const normalized = markdown.replace(/\r\n/g, '\n');
  if (!normalized.startsWith('---\n')) {
    return normalized;
  }

  const end = normalized.indexOf('\n---\n', 4);
  if (end === -1) {
    return normalized;
  }

  return normalized.slice(end + 5).trim();
};

const toBlocks = (markdown: string): MarkdownBlock[] => {
  const content = stripFrontmatter(markdown);
  const lines = content.split('\n');
  const blocks: MarkdownBlock[] = [];
  let paragraphBuffer: string[] = [];

  const flushParagraph = () => {
    if (!paragraphBuffer.length) {
      return;
    }
    blocks.push({ type: 'p', content: paragraphBuffer.join(' ').trim() });
    paragraphBuffer = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      return;
    }

    if (line === '---') {
      flushParagraph();
      blocks.push({ type: 'hr' });
      return;
    }

    if (line.startsWith('## ')) {
      flushParagraph();
      blocks.push({ type: 'h2', content: line.slice(3).trim() });
      return;
    }

    if (line.startsWith('# ')) {
      flushParagraph();
      blocks.push({ type: 'h1', content: line.slice(2).trim() });
      return;
    }

    paragraphBuffer.push(line);
  });

  flushParagraph();
  return blocks;
};

const renderInline = (text: string): React.ReactNode[] => {
  const parts: React.ReactNode[] = [];
  const boldSplit = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);

  boldSplit.forEach((segment, index) => {
    const isBold = segment.startsWith('**') && segment.endsWith('**');
    const value = isBold ? segment.slice(2, -2) : segment;
    const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;

    let lastIndex = 0;
    let match = linkRegex.exec(value);
    const fragment: React.ReactNode[] = [];

    while (match) {
      if (match.index > lastIndex) {
        fragment.push(value.slice(lastIndex, match.index));
      }
      fragment.push(
        <a
          key={`link-${index}-${match.index}`}
          href={match[2]}
          target="_blank"
          rel="noreferrer"
          className="underline underline-offset-4 decoration-black/40 hover:decoration-black"
        >
          {match[1]}
        </a>,
      );
      lastIndex = match.index + match[0].length;
      match = linkRegex.exec(value);
    }

    if (lastIndex < value.length) {
      fragment.push(value.slice(lastIndex));
    }

    parts.push(
      isBold ? <strong key={`strong-${index}`}>{fragment}</strong> : <React.Fragment key={`text-${index}`}>{fragment}</React.Fragment>,
    );
  });

  return parts;
};

export const Blog: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [posts, setPosts] = useState<BlogPostMeta[]>([]);
  const [selectedMarkdown, setSelectedMarkdown] = useState('');
  const [isLoadingPosts, setIsLoadingPosts] = useState(true);
  const [isLoadingPost, setIsLoadingPost] = useState(false);
  const [indexError, setIndexError] = useState('');
  const [postError, setPostError] = useState('');

  const selectedSlug = searchParams.get('post');

  useEffect(() => {
    document.title = 'US Fashion Trend Blog | ZuzuMood';
  }, []);

  useEffect(() => {
    const loadIndex = async () => {
      setIsLoadingPosts(true);
      setIndexError('');

      try {
        const response = await fetch(toAssetUrl('/blog/index.json'), { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`Blog index could not be loaded (${response.status})`);
        }

        const data = (await response.json()) as BlogPostMeta[];
        setPosts(Array.isArray(data) ? data : []);
      } catch (error) {
        setPosts([]);
        setIndexError(error instanceof Error ? error.message : 'Blog index could not be loaded.');
      } finally {
        setIsLoadingPosts(false);
      }
    };

    void loadIndex();
  }, []);

  useEffect(() => {
    if (!selectedSlug && posts.length > 0) {
      setSearchParams({ post: posts[0].slug }, { replace: true });
    }
  }, [posts, selectedSlug, setSearchParams]);

  useEffect(() => {
    const selectedPost = posts.find((post) => post.slug === selectedSlug) ?? posts[0];

    if (!selectedPost) {
      setSelectedMarkdown('');
      return;
    }

    const loadPost = async () => {
      setIsLoadingPost(true);
      setPostError('');
      try {
        const response = await fetch(toAssetUrl(selectedPost.path), { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`Blog post could not be loaded (${response.status})`);
        }

        const markdown = await response.text();
        setSelectedMarkdown(markdown);
      } catch (error) {
        setSelectedMarkdown('');
        setPostError(error instanceof Error ? error.message : 'Blog post could not be loaded.');
      } finally {
        setIsLoadingPost(false);
      }
    };

    void loadPost();
  }, [posts, selectedSlug]);

  const selectedPost = useMemo(
    () => posts.find((post) => post.slug === selectedSlug) ?? posts[0],
    [posts, selectedSlug],
  );

  const blocks = useMemo(() => toBlocks(selectedMarkdown), [selectedMarkdown]);

  return (
    <div className="bg-neutral-50 pt-28 md:pt-36 pb-20 px-6">
      <div className="container mx-auto">
        <section className="bg-black text-white rounded-3xl p-8 md:p-14 mb-10">
          <p className="text-[10px] uppercase tracking-[0.35em] text-white/70 mb-5">Daily SEO Trend Engine • America/Texas Focus</p>
          <h1 className="text-3xl md:text-5xl font-serif mb-5">ZuzuMood Fashion Trend Blog</h1>
          <p className="max-w-3xl text-sm md:text-base text-white/85 leading-relaxed">
            Bu sayfa her gün ABD moda trendlerini analiz ederek Etsy satış SEO odaklı içerik üretir.
            Her yazı, arama motorlarından gelen moda trafiğini ZuzuMood Etsy mağazamıza yönlendirmek için optimize edilir.
          </p>
          <div className="mt-7 flex flex-wrap gap-4">
            <a
              href="https://www.etsy.com/shop/ZuzuMood"
              target="_blank"
              rel="noreferrer"
              className="inline-block bg-white text-black px-6 py-3 text-[11px] font-bold uppercase tracking-[0.25em]"
            >
              Visit Etsy Store
            </a>
            <Link to="/shop" className="inline-block border border-white/60 px-6 py-3 text-[11px] font-bold uppercase tracking-[0.25em]">
              Shop Collection
            </Link>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-8 items-start">
          <aside className="bg-white rounded-2xl border border-gray-100 p-5 md:p-6 lg:sticky lg:top-36">
            <h2 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-4 text-muted">Latest Blog Posts</h2>
            {isLoadingPosts ? (
              <p className="text-sm text-muted">Blog index loading...</p>
            ) : indexError ? (
              <p className="text-sm text-red-600">{indexError}</p>
            ) : (
              <ul className="space-y-3">
                {posts.map((post) => {
                  const isActive = post.slug === selectedPost?.slug;
                  return (
                    <li key={post.slug}>
                      <button
                        type="button"
                        onClick={() => setSearchParams({ post: post.slug })}
                        className={`w-full text-left rounded-xl border p-4 transition-all ${
                          isActive
                            ? 'border-black bg-black text-white'
                            : 'border-gray-200 bg-white hover:border-black/50'
                        }`}
                      >
                        <p className="text-[10px] uppercase tracking-[0.22em] mb-2 opacity-80">
                          {new Date(post.date).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </p>
                        <p className="font-serif leading-tight text-lg">{post.title}</p>
                        <p className={`text-xs mt-2 leading-relaxed ${isActive ? 'text-white/85' : 'text-muted'}`}>{post.summary}</p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </aside>

          <article className="bg-white rounded-2xl border border-gray-100 p-6 md:p-10">
            {selectedPost?.image && (
              <img
                src={toAssetUrl(selectedPost.image)}
                alt={selectedPost.title}
                className="w-full h-52 md:h-72 object-cover rounded-2xl mb-8 border border-gray-100"
                loading="lazy"
              />
            )}

            {isLoadingPost ? (
              <p className="text-base text-muted">Post loading...</p>
            ) : postError ? (
              <p className="text-base text-red-600">{postError}</p>
            ) : (
              <div className="space-y-6 text-gray-900">
                {blocks.map((block, index) => {
                  if (block.type === 'h1') {
                    return <h1 key={index} className="text-3xl md:text-5xl font-serif leading-tight">{block.content}</h1>;
                  }

                  if (block.type === 'h2') {
                    return <h2 key={index} className="text-2xl font-serif pt-4 border-t border-gray-100">{block.content}</h2>;
                  }

                  if (block.type === 'hr') {
                    return <hr key={index} className="border-gray-200 my-4" />;
                  }

                  return (
                    <p key={index} className="text-[15px] leading-8 text-gray-700">
                      {block.content ? renderInline(block.content) : ''}
                    </p>
                  );
                })}
              </div>
            )}

            <div className="mt-10 rounded-2xl bg-neutral-100 p-6 border border-gray-200">
              <h3 className="text-xl font-serif mb-2">Ready to shop the trend?</h3>
              <p className="text-sm text-gray-700 mb-4">Blogdaki ABD trendlerini ZuzuMood Etsy mağazamızdaki tasarımlarla hemen eşleştirin.</p>
              <a
                href="https://www.etsy.com/shop/ZuzuMood"
                target="_blank"
                rel="noreferrer"
                className="inline-block bg-black text-white px-6 py-3 text-[11px] uppercase tracking-[0.25em] font-bold"
              >
                Go to Etsy Shop
              </a>
            </div>
          </article>
        </div>
      </div>
    </div>
  );
};
