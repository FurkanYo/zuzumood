import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

interface AdminPostMeta {
  slug: string;
  title: string;
  summary: string;
  date: string;
  path: string;
}

interface MarkdownBlock {
  type: 'h1' | 'h2' | 'p' | 'hr';
  content?: string;
}

const BASE_URL = import.meta.env.BASE_URL || '/';
const ADMIN_PASSWORD = 'zuzumood';
const ADMIN_AUTH_STORAGE_KEY = 'zuzumood-admin-auth';

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

export const Admin: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [posts, setPosts] = useState<AdminPostMeta[]>([]);
  const [selectedMarkdown, setSelectedMarkdown] = useState('');
  const [isLoadingPosts, setIsLoadingPosts] = useState(true);
  const [isLoadingPost, setIsLoadingPost] = useState(false);
  const [indexError, setIndexError] = useState('');
  const [postError, setPostError] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    typeof window !== 'undefined' && window.sessionStorage.getItem(ADMIN_AUTH_STORAGE_KEY) === 'ok',
  );

  const selectedSlug = searchParams.get('post');

  useEffect(() => {
    document.title = 'ZuzuMood Admin Trend Desk';

    const previousRobots = document.querySelector('meta[name="robots"]');
    const previousContent = previousRobots?.getAttribute('content') ?? null;

    let robotsTag = previousRobots;
    if (!robotsTag) {
      robotsTag = document.createElement('meta');
      robotsTag.setAttribute('name', 'robots');
      document.head.appendChild(robotsTag);
    }
    robotsTag.setAttribute('content', 'noindex, nofollow, noarchive');

    return () => {
      if (robotsTag) {
        if (previousContent) {
          robotsTag.setAttribute('content', previousContent);
        } else if (!previousRobots) {
          robotsTag.remove();
        }
      }
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const loadIndex = async () => {
      setIsLoadingPosts(true);
      setIndexError('');

      try {
        const response = await fetch(toAssetUrl('/admin/index.json'), { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`Admin index could not be loaded (${response.status})`);
        }

        const data = (await response.json()) as AdminPostMeta[];
        setPosts(Array.isArray(data) ? data : []);
      } catch (error) {
        setPosts([]);
        setIndexError(error instanceof Error ? error.message : 'Admin index could not be loaded.');
      } finally {
        setIsLoadingPosts(false);
      }
    };

    void loadIndex();
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    if (!selectedSlug && posts.length > 0) {
      setSearchParams({ post: posts[0].slug }, { replace: true });
    }
  }, [isAuthenticated, posts, selectedSlug, setSearchParams]);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

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
          throw new Error(`Admin report could not be loaded (${response.status})`);
        }

        const markdown = await response.text();
        setSelectedMarkdown(markdown);
      } catch (error) {
        setSelectedMarkdown('');
        setPostError(error instanceof Error ? error.message : 'Admin report could not be loaded.');
      } finally {
        setIsLoadingPost(false);
      }
    };

    void loadPost();
  }, [isAuthenticated, posts, selectedSlug]);

  const selectedPost = useMemo(
    () => posts.find((post) => post.slug === selectedSlug) ?? posts[0],
    [posts, selectedSlug],
  );

  const blocks = useMemo(() => toBlocks(selectedMarkdown), [selectedMarkdown]);

  const handleSubmitPassword = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (passwordInput.trim() !== ADMIN_PASSWORD) {
      setPasswordError('Şifre hatalı.');
      return;
    }

    window.sessionStorage.setItem(ADMIN_AUTH_STORAGE_KEY, 'ok');
    setIsAuthenticated(true);
    setPasswordError('');
    setPasswordInput('');
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-neutral-50 min-h-screen pt-28 md:pt-36 pb-20 px-6">
        <div className="max-w-lg mx-auto bg-white rounded-2xl border border-gray-200 p-8">
          <h1 className="text-3xl font-serif mb-4">ZuzuMood Admin Giriş</h1>
          <p className="text-sm text-gray-700 mb-6">Bu sayfa yalnızca şirket içi trend rehberi için kullanılır. Devam etmek için şifre girin.</p>
          <form onSubmit={handleSubmitPassword} className="space-y-4">
            <input
              type="password"
              value={passwordInput}
              onChange={(event) => setPasswordInput(event.target.value)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm"
              placeholder="Şifre"
              autoComplete="current-password"
            />
            {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
            <button
              type="submit"
              className="w-full bg-black text-white px-6 py-3 text-[11px] uppercase tracking-[0.25em] font-bold rounded-xl"
            >
              Giriş Yap
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-neutral-50 pt-28 md:pt-36 pb-20 px-6">
      <div className="max-w-7xl mx-auto">
        <section className="bg-black text-white rounded-3xl p-8 md:p-14 mb-10">
          <p className="text-[10px] uppercase tracking-[0.35em] text-white/70 mb-5">Internal Trend Desk • US Market / Etsy Demand</p>
          <h1 className="text-3xl md:text-5xl font-serif mb-5">ZuzuMood Admin Trend Rehberi</h1>
          <p className="max-w-3xl text-sm md:text-base text-white/85 leading-relaxed">
            Bu panel günlük olarak ABD moda sinyallerini, Etsy satış fırsatlarını ve 15/20/30 gün sonrası trend tahminlerini Türkçe olarak toplar.
            House tasarım ekibi bu raporları kullanarak koleksiyon fikirlerini hızlıca planlayabilir.
          </p>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-8 items-start">
          <aside className="bg-white rounded-2xl border border-gray-100 p-5 md:p-6 lg:sticky lg:top-36">
            <h2 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-4 text-muted">Admin Raporları</h2>
            {isLoadingPosts ? (
              <p className="text-sm text-muted">Rapor listesi yükleniyor...</p>
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
                          {new Date(post.date).toLocaleDateString('tr-TR', {
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

          <article className="min-w-0 bg-white rounded-2xl border border-gray-100 p-6 md:p-10 overflow-hidden">
            {isLoadingPost ? (
              <p className="text-base text-muted">Rapor yükleniyor...</p>
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
          </article>
        </div>
      </div>
    </div>
  );
};
