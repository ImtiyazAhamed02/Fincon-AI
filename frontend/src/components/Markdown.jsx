import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Markdown({ content }) {
  if (!content) return null;

  return (
    <div className="premium-markdown text-sm leading-relaxed font-sans"
      style={{ color: 'var(--text-secondary)' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ ...props }) => (
            <h1 className="text-sm font-black mt-5 mb-3 pb-1.5"
              style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border-subtle)' }}
              {...props} />
          ),
          h2: ({ ...props }) => (
            <h2 className="text-xs font-bold mt-4 mb-2 uppercase tracking-wider"
              style={{ color: 'var(--text-primary)' }}
              {...props} />
          ),
          h3: ({ ...props }) => (
            <h3 className="text-xs font-semibold mt-3 mb-1"
              style={{ color: 'var(--text-secondary)' }}
              {...props} />
          ),
          p: ({ ...props }) => <p className="mb-3 last:mb-0" {...props} />,
          ul: ({ ...props }) => (
            <ul className="list-disc pl-5 mb-3 space-y-1.5" style={{ color: 'var(--text-secondary)' }} {...props} />
          ),
          ol: ({ ...props }) => (
            <ol className="list-decimal pl-5 mb-3 space-y-1.5" style={{ color: 'var(--text-secondary)' }} {...props} />
          ),
          li: ({ ...props }) => <li className="pl-0.5" {...props} />,
          strong: ({ ...props }) => <strong style={{ color: 'var(--text-primary)', fontWeight: 700 }} {...props} />,
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-4 px-4 py-2.5 rounded-r-xl my-4 text-xs italic leading-relaxed"
              style={{
                borderColor: 'var(--accent-blue)',
                background: 'rgba(79, 139, 255, 0.06)',
                color: 'var(--text-secondary)',
              }}
              {...props} />
          ),
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-4 rounded-xl" style={{ border: '1px solid var(--border-subtle)' }}>
              <table className="w-full text-left border-collapse text-[11px]" {...props} />
            </div>
          ),
          thead: ({ ...props }) => (
            <thead style={{
              background: 'var(--bg-elevated)',
              borderBottom: '1px solid var(--border-subtle)',
              color: 'var(--text-tertiary)',
            }} {...props} />
          ),
          tbody: ({ ...props }) => <tbody {...props} />,
          tr: ({ ...props }) => (
            <tr className="transition-colors" style={{ borderBottom: '1px solid var(--border-subtle)' }} {...props} />
          ),
          th: ({ ...props }) => (
            <th className="px-3 py-2 font-bold" style={{ color: 'var(--text-primary)' }} {...props} />
          ),
          td: ({ ...props }) => (
            <td className="px-3 py-2 align-middle" style={{ color: 'var(--text-secondary)' }} {...props} />
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className || !className.includes('language-');
            return isInline ? (
              <code className="px-1.5 py-0.5 rounded text-[11px] font-mono"
                style={{
                  background: 'var(--bg-elevated)',
                  color: 'var(--accent-blue)',
                  border: '1px solid var(--border-subtle)',
                }}
                {...props}>
                {children}
              </code>
            ) : (
              <code className="block p-3.5 rounded-xl font-mono text-[11px] overflow-x-auto my-3"
                style={{
                  background: 'var(--bg-elevated)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
                {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
