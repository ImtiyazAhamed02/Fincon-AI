import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Markdown({ content }) {
  if (!content) return null;

  return (
    <div className="premium-markdown text-sm text-slate-300 leading-relaxed font-sans">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ ...props }) => <h1 className="text-sm font-black text-white mt-5 mb-3 border-b border-white/5 pb-1.5" {...props} />,
          h2: ({ ...props }) => <h2 className="text-xs font-bold text-white mt-4 mb-2 uppercase tracking-wider" {...props} />,
          h3: ({ ...props }) => <h3 className="text-xs font-semibold text-slate-200 mt-3 mb-1" {...props} />,
          p: ({ ...props }) => <p className="mb-3 last:mb-0" {...props} />,
          ul: ({ ...props }) => <ul className="list-disc pl-5 mb-3 space-y-1.5 text-slate-300" {...props} />,
          ol: ({ ...props }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5 text-slate-300" {...props} />,
          li: ({ ...props }) => <li className="pl-0.5" {...props} />,
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-4 border-blue-500 bg-blue-950/20 px-4 py-2.5 rounded-r-xl my-4 text-xs italic text-slate-300 leading-relaxed" {...props} />
          ),
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-4 rounded-xl border border-white/5 bg-slate-950/20">
              <table className="w-full text-left border-collapse text-[11px]" {...props} />
            </div>
          ),
          thead: ({ ...props }) => <thead className="bg-slate-900/60 border-b border-white/5 text-slate-400 font-semibold" {...props} />,
          tbody: ({ ...props }) => <tbody className="divide-y divide-white/5" {...props} />,
          tr: ({ ...props }) => <tr className="hover:bg-white/[0.01] transition-colors" {...props} />,
          th: ({ ...props }) => <th className="px-3 py-2 font-bold text-white" {...props} />,
          td: ({ ...props }) => <td className="px-3 py-2 text-slate-300 align-middle" {...props} />,
          code: ({ className, children, ...props }) => {
            const isInline = !className || !className.includes('language-');
            return isInline ? (
              <code className="bg-slate-800/50 px-1.5 py-0.5 rounded text-[11px] font-mono text-blue-400" {...props}>
                {children}
              </code>
            ) : (
              <code className="block bg-slate-950/40 p-3.5 rounded-xl font-mono text-[11px] text-slate-300 overflow-x-auto border border-white/5 my-3" {...props}>
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
