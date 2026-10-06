import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Upload, Send, BrainCircuit, BookOpen, Layers, Loader2, Plus, Trash2, MessageSquare, X, CheckCircle2, XCircle } from 'lucide-react';

export default function App() {
  const [strategy, setStrategy] = useState("standard");
  const [question, setQuestion] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // --- DATABASE STATE ---
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);

  // --- QUIZ STATE ---
  const [isQuizLoading, setIsQuizLoading] = useState(false);
  const [quizData, setQuizData] = useState(null);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [selectedAnswerIndex, setSelectedAnswerIndex] = useState(null);
  const [quizScore, setQuizScore] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);
  
  // --- TOPIC PROMPT STATE ---
  const [showTopicPrompt, setShowTopicPrompt] = useState(false);
  const [quizTopic, setQuizTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(3); // NEW: Track the requested number of questions

  const fileInputRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await axios.get("http://localhost:8000/sessions");
        if (res.data.length > 0) {
          setSessions(res.data);
          setActiveId(res.data[0].id); 
        } else {
          createNewSession(); 
        }
      } catch (err) {
        console.error("Failed to connect to database", err);
      }
    };
    fetchSessions();
  }, []);

  useEffect(() => {
    if (!activeId) return;
    const fetchMessages = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/sessions/${activeId}/messages`);
        setMessages(res.data);
      } catch (err) {
        console.error("Failed to load messages", err);
      }
    };
    fetchMessages();
  }, [activeId]);

  const createNewSession = async () => {
    try {
      const res = await axios.post("http://localhost:8000/sessions");
      setSessions(prev => [res.data, ...prev]);
      setActiveId(res.data.id);
    } catch (err) {
      console.error("Failed to create session", err);
    }
  };

  const handleClearChat = async () => {
    if (!activeId) return;
    if (window.confirm("Are you sure you want to permanently delete this study session?")) {
      try {
        await axios.delete(`http://localhost:8000/sessions/${activeId}`);
        const remaining = sessions.filter(s => s.id !== activeId);
        setSessions(remaining);
        
        if (remaining.length > 0) {
          setActiveId(remaining[0].id);
        } else {
          createNewSession();
        }
      } catch (err) {
        console.error("Failed to delete session", err);
      }
    }
  };

  const handleUploadClick = () => fileInputRef.current.click();

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploadStatus("Uploading & Embedding...");
      const response = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setUploadStatus(`Success: ${response.data.chunks_added} chunks embedded!`);
      setTimeout(() => setUploadStatus(""), 5000);
    } catch (error) {
      setUploadStatus("Upload failed. Backend running?");
      setTimeout(() => setUploadStatus(""), 5000);
    }
    e.target.value = null; 
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!question.trim() || !activeId) return;

    const userQuestion = question;
    setQuestion("");
    setIsLoading(true);

    setMessages(prev => [...prev, { role: "user", text: userQuestion }]);

    try {
      const response = await axios.post("http://localhost:8000/chat", {
        session_id: activeId,
        question: userQuestion,
        strategy: strategy
      });

      setMessages(prev => [...prev, { 
        role: "assistant", 
        text: response.data.answer, 
        sources: response.data.sources 
      }]);

      const sessionsRes = await axios.get("http://localhost:8000/sessions");
      setSessions(sessionsRes.data);
      
    } catch (error) {
      setMessages(prev => [...prev, { role: "assistant", text: "Error connecting to the server." }]);
    }
    setIsLoading(false);
  };

  const openTopicPrompt = () => {
    setQuizTopic("");
    setNumQuestions(3); // Reset to default on open
    setShowTopicPrompt(true);
  };

  const submitQuizTopic = async (e) => {
    e.preventDefault();
    if (!quizTopic.trim()) return;

    setShowTopicPrompt(false);
    setIsQuizLoading(true);
    try {
      // NEW: Pass the dynamically selected number to the backend
      const response = await axios.post("http://localhost:8000/quiz", {
        topic: quizTopic,
        num_questions: Number(numQuestions) 
      });
      
      setQuizData(response.data.questions);
      setCurrentQuizIndex(0);
      setSelectedAnswerIndex(null);
      setQuizScore(0);
      setQuizCompleted(false);
      setShowQuizModal(true);
    } catch (error) {
      console.error(error);
      alert("Failed to generate quiz. Make sure notes are uploaded and the topic is covered.");
    }
    setIsQuizLoading(false);
  };

  const handleAnswerSelect = (optionIndex, isCorrect) => {
    if (selectedAnswerIndex !== null) return;
    
    setSelectedAnswerIndex(optionIndex);
    if (isCorrect) setQuizScore(prev => prev + 1);
  };

  const handleNextQuestion = () => {
    if (currentQuizIndex < quizData.length - 1) {
      setCurrentQuizIndex(prev => prev + 1);
      setSelectedAnswerIndex(null);
    } else {
      setQuizCompleted(true);
    }
  };

  const closeQuizModal = () => {
    setShowQuizModal(false);
    setTimeout(() => {
        setQuizData(null);
    }, 300);
  };


  return (
    <div className="flex h-screen bg-slate-950 text-slate-300 font-sans selection:bg-cyan-500/30 relative">
      
      {/* LEFT SIDEBAR */}
      <div className="w-80 bg-slate-900/40 backdrop-blur-xl border-r border-slate-800/60 p-6 flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.5)] z-20">
        
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-extrabold flex items-center gap-3 tracking-tight">
            <BookOpen className="text-cyan-400" size={24} />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent text-xl">
              Study Assistant
            </span>
          </h1>
          <button onClick={createNewSession} className="p-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg transition-colors border border-slate-700/50 shadow-sm" title="New Chat">
            <Plus size={20} />
          </button>
        </div>

        <button onClick={handleUploadClick} className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3.5 rounded-xl hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] hover:scale-[1.02] transition-all duration-300 mb-2 border border-white/10">
          <Upload size={18} /> Upload PDF Notes
        </button>
        <input type="file" accept="application/pdf" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
        <div className="h-6 mb-2 text-center">
          {uploadStatus && <span className="text-xs font-semibold text-cyan-400 animate-pulse tracking-wide">{uploadStatus}</span>}
        </div>

        <div className="mb-6">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 block flex items-center gap-2">
            <Layers size={14} /> Retrieval Strategy
          </label>
          <div className="flex bg-slate-900/80 p-1.5 rounded-xl border border-slate-800 shadow-inner">
            <button onClick={() => setStrategy("standard")} className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all duration-300 ${strategy === "standard" ? "bg-slate-800 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.1)] border border-slate-700/50" : "text-slate-500 hover:text-slate-300"}`}>Standard</button>
            <button onClick={() => setStrategy("rerank")} className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all duration-300 ${strategy === "rerank" ? "bg-slate-800 text-purple-400 shadow-[0_0_10px_rgba(168,85,247,0.1)] border border-slate-700/50" : "text-slate-500 hover:text-slate-300"}`}>Rerank</button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto pr-2 space-y-2 mb-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 block">Recent Chats</label>
          {sessions.map(session => (
            <button 
              key={session.id}
              onClick={() => setActiveId(session.id)}
              className={`w-full text-left flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 text-sm ${
                activeId === session.id 
                  ? "bg-slate-800/80 text-cyan-300 border border-slate-700/50" 
                  : "text-slate-400 hover:bg-slate-800/40 hover:text-slate-200"
              }`}
            >
              <MessageSquare size={16} className={activeId === session.id ? "text-cyan-500" : "text-slate-500"} flex-shrink-0/>
              <span className="truncate">{session.title}</span>
            </button>
          ))}
        </div>

        <button 
          onClick={openTopicPrompt} 
          disabled={isQuizLoading}
          className="w-full flex items-center justify-center gap-2 bg-slate-900 border border-slate-700 text-slate-300 py-3.5 rounded-xl hover:bg-slate-800 hover:border-cyan-500/50 hover:text-cyan-400 hover:shadow-[0_0_15px_rgba(34,211,238,0.2)] transition-all duration-300 font-medium disabled:opacity-50"
        >
          {isQuizLoading ? <Loader2 className="animate-spin" size={18} /> : <BrainCircuit size={18} />} 
          {isQuizLoading ? "Generating..." : "Generate Quiz"}
        </button>
      </div>

      {/* RIGHT MAIN WINDOW */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        <div className="absolute top-0 w-full p-4 flex justify-end z-30 pointer-events-none">
           <button 
             onClick={handleClearChat} 
             disabled={messages.length === 0}
             className="pointer-events-auto flex items-center gap-2 px-4 py-2 bg-slate-900/60 hover:bg-red-900/40 text-slate-400 hover:text-red-400 rounded-lg backdrop-blur-md border border-slate-800 hover:border-red-500/30 transition-all duration-300 text-sm font-medium disabled:opacity-0"
           >
             <Trash2 size={16} /> Delete Chat
           </button>
        </div>

        <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-cyan-600/10 rounded-full blur-[120px] pointer-events-none"></div>

        <div ref={chatContainerRef} className="flex-1 p-8 pt-20 overflow-y-auto flex flex-col gap-6 relative z-10 pb-8">
           {messages.length === 0 ? (
             <div className="m-auto text-center space-y-4">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-900 border border-slate-800 shadow-[0_0_30px_rgba(0,0,0,0.5)] mb-2">
                  <BookOpen className="text-slate-600" size={28} />
                </div>
                <p className="text-slate-500 font-medium">Start a new study session...</p>
             </div>
           ) : (
             messages.map((msg, index) => (
               <div key={index} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                 <div className={`max-w-[80%] rounded-2xl p-5 ${msg.role === "user" ? "bg-gradient-to-br from-cyan-600 to-blue-600 text-white shadow-lg" : "bg-slate-900/80 border border-slate-700 text-slate-200 shadow-md backdrop-blur-sm"}`}>
                   <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                   {msg.sources && msg.sources.length > 0 && (
                     <div className="mt-3 pt-3 border-t border-slate-700 flex gap-2 text-xs font-mono text-cyan-400">
                       <span className="text-slate-500">Sources:</span> {msg.sources.join(", ")}
                     </div>
                   )}
                 </div>
               </div>
             ))
           )}
           {isLoading && (
             <div className="flex items-center gap-2 text-slate-500 font-medium">
               <Loader2 className="animate-spin" size={16} /> Retrieving context...
             </div>
           )}
        </div>
        
        <div className="p-6 relative z-10 bg-gradient-to-t from-slate-950 to-transparent">
          <form onSubmit={handleChat} className="flex gap-4 max-w-4xl mx-auto">
            <input 
              type="text" 
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your notes..." 
              className="flex-1 bg-slate-900/90 border border-slate-700 rounded-2xl px-6 py-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:shadow-[0_0_20px_rgba(34,211,238,0.15)] transition-all duration-300"
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading} className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-8 py-4 rounded-2xl hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:scale-[1.05] transition-all duration-300 flex items-center justify-center border border-white/10 disabled:opacity-50 disabled:hover:scale-100">
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>

      {/* TOPIC PROMPT MODAL */}
      {showTopicPrompt && (
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl w-full max-w-md p-6 relative animate-in fade-in zoom-in duration-200">
            <button onClick={() => setShowTopicPrompt(false)} className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition-colors">
              <X size={20} />
            </button>
            <h2 className="text-xl font-bold text-cyan-400 mb-2 flex items-center gap-2">
              <BrainCircuit size={20} /> Generate Quiz
            </h2>
            <p className="text-slate-400 text-sm mb-6">Set up your custom assessment below.</p>
            
            <form onSubmit={submitQuizTopic}>
              <div className="mb-4">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Topic</label>
                <input 
                  type="text" 
                  value={quizTopic}
                  onChange={(e) => setQuizTopic(e.target.value)}
                  placeholder="e.g., The Mali Empire, Abolition..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
                  autoFocus
                />
              </div>

              {/* NEW: Dropdown to select question count */}
              <div className="mb-6">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Number of Questions</label>
                <div className="relative">
                  <select 
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-cyan-500 appearance-none cursor-pointer"
                  >
                    <option value={3}>3 Questions (Quick Review)</option>
                    <option value={5}>5 Questions (Standard Practice)</option>
                    <option value={10}>10 Questions (Full Exam)</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                  </div>
                </div>
              </div>

              <button 
                type="submit" 
                disabled={!quizTopic.trim()}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold py-3 rounded-xl disabled:opacity-50 hover:shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-all"
              >
                Start Quiz
              </button>
            </form>
          </div>
        </div>
      )}

      {/* QUIZ MODAL OVERLAY */}
      {showQuizModal && (
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl w-full max-w-2xl overflow-hidden flex flex-col relative animate-in fade-in zoom-in duration-200">
            
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
              <h2 className="text-xl font-bold flex items-center gap-2 text-cyan-400">
                <BrainCircuit size={20} /> Concept Verification
              </h2>
              <button onClick={closeQuizModal} className="text-slate-500 hover:text-slate-300 transition-colors">
                <X size={24} />
              </button>
            </div>

            <div className="p-8">
              {quizCompleted ? (
                 <div className="text-center py-10 space-y-4">
                    <h3 className="text-3xl font-extrabold text-white">Quiz Complete!</h3>
                    <p className="text-slate-400 text-lg">You scored <span className="text-cyan-400 font-bold">{quizScore}</span> out of {quizData.length}</p>
                    <div className="mt-8">
                      <button onClick={closeQuizModal} className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-8 py-3 rounded-xl font-medium hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] transition-all">
                        Return to Study Session
                      </button>
                    </div>
                 </div>
              ) : quizData ? (
                 <div className="space-y-6">
                    <div className="flex justify-between items-center text-sm font-medium text-slate-500 mb-2">
                       <span>Question {currentQuizIndex + 1} of {quizData.length}</span>
                       <span>Score: {quizScore}</span>
                    </div>
                    
                    <h3 className="text-lg font-medium leading-relaxed text-slate-200">
                      {quizData[currentQuizIndex].question}
                    </h3>

                    <div className="space-y-3 mt-6">
                      {quizData[currentQuizIndex].options.map((option, idx) => {
                        let buttonStyle = "bg-slate-800 border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/80 text-slate-300";
                        
                        if (selectedAnswerIndex !== null) {
                           if (option.is_correct) {
                             buttonStyle = "bg-green-900/40 border-green-500 text-green-100 shadow-[0_0_15px_rgba(34,197,94,0.2)]";
                           } else if (selectedAnswerIndex === idx) {
                             buttonStyle = "bg-red-900/40 border-red-500 text-red-100";
                           } else {
                             buttonStyle = "bg-slate-900/50 border-slate-800 text-slate-600 opacity-50";
                           }
                        }

                        return (
                          <button
                            key={idx}
                            onClick={() => handleAnswerSelect(idx, option.is_correct)}
                            disabled={selectedAnswerIndex !== null}
                            className={`w-full text-left p-4 rounded-xl border transition-all duration-300 flex justify-between items-center ${buttonStyle}`}
                          >
                            <span>{option.text}</span>
                            {selectedAnswerIndex !== null && option.is_correct && <CheckCircle2 size={18} className="text-green-400" />}
                            {selectedAnswerIndex === idx && !option.is_correct && <XCircle size={18} className="text-red-400" />}
                          </button>
                        );
                      })}
                    </div>

                    {selectedAnswerIndex !== null && (
                      <div className="mt-6 p-4 rounded-xl bg-slate-800/50 border border-slate-700 text-sm leading-relaxed text-slate-300">
                        <span className="font-bold text-cyan-400 uppercase text-xs tracking-wider block mb-1">Explanation</span>
                        {quizData[currentQuizIndex].explanation}
                      </div>
                    )}

                    {selectedAnswerIndex !== null && (
                      <div className="mt-8 flex justify-end">
                        <button onClick={handleNextQuestion} className="bg-white text-slate-900 px-6 py-2.5 rounded-lg font-semibold hover:bg-slate-200 transition-colors">
                          {currentQuizIndex < quizData.length - 1 ? "Next Question" : "See Results"}
                        </button>
                      </div>
                    )}
                 </div>
              ) : (
                <div className="py-20 text-center text-slate-500">Error loading quiz data.</div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}