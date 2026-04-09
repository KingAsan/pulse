import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  useAIRecommendations,
  useAISessions,
  useAIChatHistory,
  useAIFeedback,
  useAIOnboardingStatus,
  useCompleteAIOnboarding,
  useAIInsights,
} from '../hooks/useAI'
import { SkeletonChatMessage } from '../components/common/Skeleton'
import './AIPage.css'

export default function AIPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [showSessions, setShowSessions] = useState(false)
  const messagesEndRef = useRef(null)

  // AI Hooks
  const recommendMutation = useAIRecommendations()
  const { data: sessions, isLoading: sessionsLoading } = useAISessions()
  const { data: chatHistory, isLoading: historyLoading } = useAIChatHistory(sessionId)
  const feedbackMutation = useAIFeedback()
  const { data: onboardingStatus } = useAIOnboardingStatus()
  const completeOnboarding = useCompleteAIOnboarding()
  const { data: insights } = useAIInsights()

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load chat history when session changes - O(n) instead of O(n^2)
  useEffect(() => {
    if (chatHistory && chatHistory.length > 0) {
      // Build a Map for O(1) lookups instead of O(n) find()
      const historyMap = new Map(chatHistory.map(msg => [msg.id, msg]))
      
      const formattedMessages = []
      
      chatHistory.forEach(msg => {
        // Add user message
        formattedMessages.push({
          id: msg.id,
          role: 'user',
          content: msg.user_query,
          timestamp: msg.timestamp,
        })
        
        // Add AI response if exists
        if (msg.ai_response) {
          formattedMessages.push({
            id: `ai-${msg.id}`,
            role: 'ai',
            content: msg.ai_response,
            recommendations: msg.ai_response_json ? JSON.parse(msg.ai_response_json) : [],
            timestamp: msg.timestamp,
          })
        }
      })
      
      setMessages(formattedMessages)
    }
  }, [chatHistory])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || recommendMutation.isPending) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setQuery('')

    try {
      const result = await recommendMutation.mutateAsync({
        query: query,
        session_id: sessionId || undefined,
      })

      const aiMessage = {
        id: Date.now() + 1,
        role: 'ai',
        content: result.recommendations
          ? formatRecommendations(result.recommendations)
          : 'Извините, я не смог подобрать рекомендации. Попробуйте другой запрос.',
        recommendations: result.recommendations || [],
        timestamp: new Date().toISOString(),
      }

      setMessages(prev => [...prev, aiMessage])
      
      // Update session ID if this is a new conversation
      if (!sessionId && result.session_id) {
        setSessionId(result.session_id)
      }
    } catch (error) {
      console.error('AI recommendation error:', error)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: 'Произошла ошибка. Пожалуйста, попробуйте снова.',
        timestamp: new Date().toISOString(),
        isError: true,
      }])
    }
  }

  const formatRecommendations = (recs) => {
    if (!recs || recs.length === 0) return ''
    
    return recs.map((rec, idx) => {
      return `**${idx + 1}. ${rec.title}** (${rec.year_genre})\n${rec.description}\n\n`
    }).join('')
  }

  const handleFeedback = (feedbackType, title, category) => {
    feedbackMutation.mutate({
      feedback_type: feedbackType,
      title,
      session_id: sessionId,
      category,
    })
  }

  const handleSessionClick = (sid) => {
    setSessionId(sid)
    setShowSessions(false)
  }

  const handleNewChat = () => {
    setSessionId(null)
    setMessages([])
    setShowSessions(false)
  }

  // Quick action buttons
  const quickActions = [
    { label: '🎬 Фильм на вечер', query: 'Посоветуй хороший фильм на вечер' },
    { label: '📚 Книгу', query: 'Какую книгу почитать?' },
    { label: '🎵 Музыку', query: 'Подбери музыку для настроения' },
    { label: '🎮 Игру', query: 'Во что поиграть?' },
  ]

  return (
    <div className="ai-page">
      {/* Header */}
      <div className="ai-header">
        <div className="ai-header-content">
          <div className="ai-title-wrap">
            <i className="ri-robot-2-line ai-icon"></i>
            <h1>AI Ассистент</h1>
          </div>
          <div className="ai-header-actions">
            {insights && (
              <div className="ai-daily-limit">
                <span className="limit-text">{insights.queries_today}/{insights.daily_limit} сегодня</span>
              </div>
            )}
            <button
              className="btn btn-sm btn-secondary"
              onClick={() => setShowSessions(!showSessions)}
            >
              <i className="ri-history-line"></i> История
            </button>
            <button
              className="btn btn-sm btn-primary"
              onClick={handleNewChat}
            >
              <i className="ri-add-line"></i> Новый чат
            </button>
          </div>
        </div>
      </div>

      <div className="ai-layout">
        {/* Sessions Sidebar */}
        {showSessions && (
          <div className="ai-sessions-sidebar">
            <div className="sessions-header">
              <h3>История чатов</h3>
              <button
                className="btn btn-sm btn-icon"
                onClick={() => setShowSessions(false)}
              >
                <i className="ri-close-line"></i>
              </button>
            </div>
            <div className="sessions-list">
              {sessionsLoading ? (
                <div className="sessions-loading">
                  <div className="spinner" />
                </div>
              ) : sessions && sessions.length > 0 ? (
                sessions.map(session => (
                  <div
                    key={session.session_id}
                    className={`session-item ${sessionId === session.session_id ? 'active' : ''}`}
                    onClick={() => handleSessionClick(session.session_id)}
                  >
                    <div className="session-icon">
                      <i className="ri-message-2-line"></i>
                    </div>
                    <div className="session-info">
                      <div className="session-title">{session.title}</div>
                      <div className="session-meta">
                        <span>{session.message_count} сообщ.</span>
                        <span>{new Date(session.last_timestamp).toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="sessions-empty">
                  <i className="ri-inbox-line"></i>
                  <p>История чатов пуста</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Chat Area */}
        <div className="ai-chat-area">
          <div className="ai-messages">
            {messages.length === 0 ? (
              <div className="ai-welcome">
                <div className="welcome-icon">
                  <i className="ri-robot-2-line"></i>
                </div>
                <h2>Привет! Я ваш AI ассистент</h2>
                <p>Я помогу подобрать фильм, книгу, музыку или игру по вашему настроению и предпочтениям</p>
                
                <div className="quick-actions">
                  <h3>Быстрые действия:</h3>
                  <div className="quick-actions-grid">
                    {quickActions.map((action, idx) => (
                      <button
                        key={idx}
                        className="quick-action-btn"
                        onClick={() => {
                          setQuery(action.query)
                        }}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="messages-list">
                {messages.map(msg => (
                  <div key={msg.id} className={`message ${msg.role} ${msg.isError ? 'error' : ''}`}>
                    <div className="message-avatar">
                      {msg.role === 'user' ? (
                        <div className="user-avatar">
                          {user?.username?.[0]?.toUpperCase() || 'U'}
                        </div>
                      ) : (
                        <div className="ai-avatar">
                          <i className="ri-robot-2-line"></i>
                        </div>
                      )}
                    </div>
                    <div className="message-content">
                      <div className="message-text">
                        {formatMarkdown(msg.content)}
                      </div>
                      
                      {/* Recommendations with feedback */}
                      {msg.role === 'ai' && msg.recommendations && msg.recommendations.length > 0 && (
                        <div className="message-recommendations">
                          {msg.recommendations.map((rec, idx) => (
                            <div key={idx} className="recommendation-card">
                              <div className="rec-content">
                                <h4>{rec.title}</h4>
                                <p className="rec-meta">{rec.year_genre} · {rec.category}</p>
                                {rec.why_this && (
                                  <p className="rec-why">💡 {rec.why_this}</p>
                                )}
                              </div>
                              <div className="rec-actions">
                                <button
                                  className="rec-btn"
                                  onClick={() => handleFeedback('like', rec.title, rec.category)}
                                  title="Нравится"
                                >
                                  <i className="ri-thumb-up-line"></i>
                                </button>
                                <button
                                  className="rec-btn"
                                  onClick={() => handleFeedback('dislike', rec.title, rec.category)}
                                  title="Не нравится"
                                >
                                  <i className="ri-thumb-down-line"></i>
                                </button>
                                <button
                                  className="rec-btn"
                                  onClick={() => handleFeedback('watched', rec.title, rec.category)}
                                  title="Просмотрено"
                                >
                                  <i className="ri-check-line"></i>
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      <div className="message-time">
                        {new Date(msg.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))}
                {recommendMutation.isPending && (
                  <div className="typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <form className="ai-input-form" onSubmit={handleSubmit}>
            <div className="input-wrapper">
              <textarea
                className="ai-input"
                placeholder="Что хотите посмотреть/почитать/послушать?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSubmit(e)
                  }
                }}
                disabled={recommendMutation.isPending}
                rows={1}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={!query.trim() || recommendMutation.isPending}
              >
                {recommendMutation.isPending ? (
                  <div className="spinner-small" />
                ) : (
                  <i className="ri-send-plane-fill"></i>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// Simple markdown formatter
function formatMarkdown(text) {
  if (!text) return ''
  
  return text
    .split('\n')
    .map(line => {
      // Bold
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic
      line = line.replace(/\*(.*?)\*/g, '<em>$1</em>')
      
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return `<li>${line.substring(2)}</li>`
      }
      if (line.startsWith('### ')) {
        return `<h4>${line.substring(4)}</h4>`
      }
      if (line.startsWith('## ')) {
        return `<h3>${line.substring(3)}</h3>`
      }
      if (line.startsWith('# ')) {
        return `<h2>${line.substring(2)}</h2>`
      }
      if (line.trim() === '') {
        return '<br/>'
      }
      return `<p>${line}</p>`
    })
    .join('')
}
