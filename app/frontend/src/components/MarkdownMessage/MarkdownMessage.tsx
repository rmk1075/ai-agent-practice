import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Props {
  content: string
}

export default function MarkdownMessage({ content }: Props) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkBreaks]}
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '')
          if (match) {
            return (
              <SyntaxHighlighter language={match[1]} style={oneLight} PreTag="div">
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            )
          }
          return <code className={className} {...props}>{children}</code>
        }
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
