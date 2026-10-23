// -*- coding: utf-8 -*-
// Component giao diện chính của ứng dụng Gợi Ý Phim (HTGoiYPhim)
// Quản lý trạng thái xác thực, danh mục phim, tìm kiếm NLP, gợi ý cá nhân hóa và phát video.

import React, { useState, useEffect } from 'react';
import './App.css';

// Đường dẫn gốc của Backend API (kết nối qua proxy hoặc trực tiếp)
const API_BASE = '/api';

function App() {
  // Trạng thái xác thực người dùng và token
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);
  
  // Trạng thái điều hướng giữa các tab: 'home' | 'for_you' | 'recommend' | 'history' | 'ratings'
  const [tab, setTab] = useState('home');
  const [movies, setMovies] = useState([]);
  const [genres, setGenres] = useState([]);
  const [selectedGenre, setSelectedGenre] = useState('All');
  
  // Trạng thái gợi ý cá nhân hóa
  const [personalizedMovies, setPersonalizedMovies] = useState([]);
  const [personalizedMsg, setPersonalizedMsg] = useState('');
  
  // Trạng thái lịch sử xem và đánh giá của người dùng
  const [history, setHistory] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  
  // Chế độ tìm kiếm: 'title' (theo tên phim) | 'plot' (theo mô tả cốt truyện AI NLP)
  const [searchMode, setSearchMode] = useState('title');
  const [searchQuery, setSearchQuery] = useState('');
  const [plotQuery, setPlotQuery] = useState('');
  const [recommendQuery, setRecommendQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Trạng thái thông báo phản hồi trên giao diện (thay thế hộp thoại alert trình duyệt)
  const [notification, setNotification] = useState(null);
  
  // Trạng thái cửa sổ xem phim
  const [playerMovie, setPlayerMovie] = useState(null);
  const [playerSource, setPlayerSource] = useState('twoembed');
  
  // Trạng thái cửa sổ đăng nhập / đăng ký
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '' });
  const [authError, setAuthError] = useState('');
  
  // Trạng thái cửa sổ đánh giá sao cho phim
  const [ratingModalMovie, setRatingModalMovie] = useState(null);
  const [ratingScore, setRatingScore] = useState(9.0);
  const [ratingComment, setRatingComment] = useState('');

  // Hàm hiển thị thông báo phản hồi tạm thời cho người dùng
  const showToast = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification(null);
    }, 4500);
  };

  // 1. Kiểm tra phiên đăng nhập của người dùng qua token
  useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(data => {
          setUser(data);
          fetchPersonalized();
        })
        .catch(() => {
          setToken('');
          localStorage.removeItem('token');
        });
    }
  }, [token]);

  // 2. Tải danh mục thể loại và danh sách phim ban đầu
  useEffect(() => {
    fetchGenres();
    fetchMovies();
  }, []);

  // Lấy danh sách thể loại từ API
  const fetchGenres = () => {
    fetch(`${API_BASE}/movies/genres`)
      .then(res => res.json())
      .then(data => setGenres(data || []))
      .catch(err => console.error('Lỗi tải thể loại:', err));
  };

  // Lấy danh sách phim theo thể loại hoặc từ khóa tìm kiếm
  const fetchMovies = (genre = 'All', search = '') => {
    setIsLoading(true);
    let url = `${API_BASE}/movies?limit=24`;
    if (genre && genre !== 'All') {
      url += `&genre=${encodeURIComponent(genre)}`;
    }
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    
    fetch(url)
      .then(res => res.json())
      .then(data => {
        setMovies(data.items || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Lỗi tải phim:', err);
        setIsLoading(false);
      });
  };

  // 3. Tải danh sách phim gợi ý cá nhân hóa dựa trên lịch sử xem và đánh giá
  const fetchPersonalized = () => {
    if (!token) return;
    fetch(`${API_BASE}/movies/personalized?top_n=12`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setPersonalizedMovies(data.recommendations || []);
        setPersonalizedMsg(data.message || '');
      })
      .catch(err => console.error('Lỗi tải gợi ý cá nhân hóa:', err));
  };

  // 4. Tìm kiếm phim theo cốt truyện tự do (AI NLP Search)
  const handlePlotSearch = (e) => {
    if (e) e.preventDefault();
    if (!plotQuery.trim()) return;
    
    setIsLoading(true);
    fetch(`${API_BASE}/movies/recommend-by-plot?query=${encodeURIComponent(plotQuery)}&top_n=20`)
      .then(res => res.json())
      .then(data => {
        setMovies(data.recommendations || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Lỗi tìm theo cốt truyện:', err);
        setIsLoading(false);
      });
  };

  // 5. Tải lịch sử xem phim của người dùng hiện tại
  const fetchHistory = () => {
    if (!token) return;
    fetch(`${API_BASE}/history?limit=50`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setHistory(data))
      .catch(err => console.error('Lỗi tải lịch sử:', err));
  };

  // Xóa một bộ phim khỏi lịch sử xem
  const handleDeleteSingleHistory = async (movieId, movieTitle) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/history/${encodeURIComponent(movieId)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast(`Đã xóa phim "${movieTitle}" khỏi lịch sử xem.`);
        fetchHistory();
        fetchPersonalized();
      } else {
        showToast('Không thể xóa phim khỏi lịch sử xem.', 'error');
      }
    } catch {
      showToast('Lỗi kết nối khi xóa phim.', 'error');
    }
  };

  // Xóa toàn bộ lịch sử xem của người dùng
  const handleClearAllHistory = async () => {
    if (!token) return;
    if (!window.confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử xem phim của mình?')) return;
    try {
      const res = await fetch(`${API_BASE}/history`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Đã xóa toàn bộ lịch sử xem thành công.');
        setHistory([]);
        fetchPersonalized();
      } else {
        showToast('Không thể xóa lịch sử xem.', 'error');
      }
    } catch {
      showToast('Lỗi kết nối khi xóa lịch sử.', 'error');
    }
  };

  // 6. Tải danh sách đánh giá của người dùng
  const fetchRatings = () => {
    if (!token) return;
    fetch(`${API_BASE}/ratings?limit=50`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setRatings(data))
      .catch(err => console.error('Lỗi tải đánh giá:', err));
  };

  // Xóa đánh giá của một bộ phim
  const handleDeleteRating = async (movieId, movieTitle) => {
    if (!token) return;
    if (!window.confirm(`Bạn có chắc chắn muốn xóa đánh giá cho phim "${movieTitle}"?`)) return;
    try {
      const res = await fetch(`${API_BASE}/ratings/${encodeURIComponent(movieId)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast(`Đã xóa đánh giá cho phim "${movieTitle}".`);
        fetchRatings();
        fetchPersonalized();
      } else {
        showToast('Không thể xóa đánh giá.', 'error');
      }
    } catch {
      showToast('Lỗi kết nối khi xóa đánh giá.', 'error');
    }
  };

  // Mở trình phát phim & Tự động lưu lịch sử xem
  const handleOpenPlayer = (movie) => {
    setPlayerMovie(movie);
    setPlayerSource('twoembed'); // Mặc định mở máy chủ 2Embed ổn định
    
    if (token) {
      fetch(`${API_BASE}/history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          movie_id: movie.id,
          movie_title: movie.title,
          poster_url: movie.poster_url
        })
      })
        .then(() => {
          fetchPersonalized();
        })
        .catch(() => {});
    }
  };

  // Xử lý Đăng ký / Đăng nhập
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    const endpoint = isRegister ? `${API_BASE}/auth/register` : `${API_BASE}/auth/login`;
    
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm)
      });
      
      const data = await res.json();
      if (!res.ok) {
        setAuthError(data.detail || 'Thao tác không thành công');
        return;
      }
      
      if (isRegister) {
        // Đăng ký xong tự động chuyển sang đăng nhập
        setIsRegister(false);
        showToast('Tạo tài khoản thành công! Vui lòng đăng nhập.');
      } else {
        // Đăng nhập thành công, lưu token vào bộ nhớ cục bộ
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        setShowAuthModal(false);
        setAuthForm({ username: '', email: '', password: '' });
        showToast(`Chào mừng ${data.user.username} đã quay trở lại.`);
      }
    } catch (err) {
      setAuthError('Không thể kết nối đến máy chủ.');
    }
  };

  // Đăng xuất và xóa token khỏi trình duyệt
  const handleLogout = () => {
    setToken('');
    setUser(null);
    localStorage.removeItem('token');
    setPersonalizedMovies([]);
    setHistory([]);
    setRatings([]);
    setTab('home');
    showToast('Đã đăng xuất khỏi tài khoản.');
  };

  // Lấy gợi ý tương đồng cho một bộ phim cụ thể
  const handleGetRecommendations = (movieTitle) => {
    setIsLoading(true);
    setTab('recommend');
    setRecommendQuery(movieTitle);
    fetch(`${API_BASE}/movies/recommendations?movie=${encodeURIComponent(movieTitle)}&top_n=12`)
      .then(res => res.json())
      .then(data => {
        setRecommendations(data.recommendations || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Lỗi gợi ý:', err);
        setIsLoading(false);
      });
  };

  // Gửi điểm đánh giá và cảm nhận cho bộ phim
  const handleSubmitRating = async () => {
    if (!token) {
      setShowAuthModal(true);
      return;
    }
    try {
      await fetch(`${API_BASE}/ratings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          movie_id: ratingModalMovie.id,
          score: parseFloat(ratingScore),
          movie_title: ratingModalMovie.title,
          poster_url: ratingModalMovie.poster_url,
          comment: ratingComment
        })
      });
      showToast(`Đã lưu đánh giá ${ratingScore}/10 cho phim "${ratingModalMovie.title}".`);
      setRatingModalMovie(null);
      fetchPersonalized();
      if (tab === 'ratings') fetchRatings();
    } catch (e) {
      showToast('Lỗi khi gửi đánh giá.', 'error');
    }
  };

  return (
    <div>
      {/* Thanh điều hướng chính (Navbar) */}
      <header className="navbar">
        <div className="logo" onClick={() => { setTab('home'); setSelectedGenre('All'); fetchMovies('All'); }}>
          <span>HTGoiYPhim</span>
        </div>
        <nav className="nav-links">
          <button className={`nav-btn ${tab === 'home' ? 'active' : ''}`} onClick={() => setTab('home')}>
            Khám phá phim
          </button>
          {token && (
            <button className={`nav-btn ${tab === 'for_you' ? 'active' : ''}`} onClick={() => { setTab('for_you'); fetchPersonalized(); }}>
              Dành cho bạn
            </button>
          )}
          <button className={`nav-btn ${tab === 'recommend' ? 'active' : ''}`} onClick={() => setTab('recommend')}>
            Gợi ý tương đồng
          </button>
          {token && (
            <>
              <button className={`nav-btn ${tab === 'history' ? 'active' : ''}`} onClick={() => { setTab('history'); fetchHistory(); }}>
                Lịch sử xem
              </button>
              <button className={`nav-btn ${tab === 'ratings' ? 'active' : ''}`} onClick={() => { setTab('ratings'); fetchRatings(); }}>
                Đánh giá của tôi
              </button>
            </>
          )}
        </nav>
        <div className="auth-box">
          {user ? (
            <>
              <span className="user-badge">{user.username}</span>
              <button className="btn-secondary" onClick={handleLogout}>Đăng xuất</button>
            </>
          ) : (
            <button className="btn-primary" onClick={() => { setShowAuthModal(true); setIsRegister(false); }}>
              Đăng nhập / Đăng ký
            </button>
          )}
        </div>
      </header>

      {/* Vùng hiển thị thông báo phản hồi */}
      <div className="container" style={{ paddingBottom: 0 }}>
        {notification && (
          <div className={`notification-banner ${notification.type}`}>
            <span>{notification.message}</span>
            <button className="notification-close" onClick={() => setNotification(null)}>Đóng</button>
          </div>
        )}
      </div>

      {/* Nội dung chính theo từng Tab */}
      <main className="container">
        {/* Tab 1: Khám phá phim */}
        {tab === 'home' && (
          <>
            {/* Khung tìm kiếm kép */}
            <div className="search-container">
              <div className="search-mode-tabs">
                <button
                  className={`search-mode-btn ${searchMode === 'title' ? 'active' : ''}`}
                  onClick={() => setSearchMode('title')}
                >
                  Tìm theo tên phim
                </button>
                <button
                  className={`search-mode-btn ${searchMode === 'plot' ? 'active' : ''}`}
                  onClick={() => setSearchMode('plot')}
                >
                  Gợi ý theo cốt truyện (AI NLP)
                </button>
              </div>

              {searchMode === 'title' ? (
                <div className="search-box">
                  <input
                    className="search-input"
                    type="text"
                    placeholder="Nhập tên phim cần tìm (ví dụ: Inception, Avatar, Titanic, Batman)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && fetchMovies(selectedGenre, searchQuery)}
                  />
                  <button className="btn-primary" onClick={() => fetchMovies(selectedGenre, searchQuery)}>Tìm kiếm</button>
                </div>
              ) : (
                <div className="search-box">
                  <input
                    className="search-input"
                    type="text"
                    placeholder="Mô tả nội dung bạn muốn xem (ví dụ: phi hành gia du hành qua lỗ sâu, sát thủ báo thù, thám tử phá án)..."
                    value={plotQuery}
                    onChange={(e) => setPlotQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handlePlotSearch(e)}
                  />
                  <button className="btn-recommend" onClick={handlePlotSearch}>Gợi ý ngay</button>
                </div>
              )}
            </div>

            {/* Mục nổi bật: Gợi ý cá nhân hóa dành riêng cho bạn */}
            {token && personalizedMovies.length > 0 && (
              <div style={{ marginBottom: '36px', background: 'rgba(229, 9, 20, 0.05)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(229, 9, 20, 0.2)' }}>
                <h2 className="section-title" style={{ color: '#f87171', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Gợi ý cá nhân hóa cho {user ? user.username : ''}</span>
                  <button className="btn-secondary" style={{ fontSize: '13px' }} onClick={() => setTab('for_you')}>Xem tất cả</button>
                </h2>
                <p style={{ color: '#9ca3af', fontSize: '13px', marginBottom: '18px' }}>{personalizedMsg}</p>
                <div className="movie-grid">
                  {personalizedMovies.slice(0, 4).map((m) => (
                    <div key={m.id} className="movie-card">
                      <div className="poster-wrap">
                        <img src={m.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'} alt={m.title} className="movie-poster" />
                        <span className="rating-badge">Điểm: {m.rating || 'N/A'}</span>
                        <span className="similarity-badge">Gu của bạn</span>
                      </div>
                      <div className="movie-info">
                        <h3 className="movie-title">{m.title}</h3>
                        <div className="movie-meta">{m.year} • {m.runtime_minutes ? `${m.runtime_minutes} phút` : ''}</div>
                        <div className="movie-genres">{m.genres}</div>
                        {m.recommendation_reason && (
                          <div className="recommendation-reason">{m.recommendation_reason}</div>
                        )}
                        <div className="card-actions">
                          <button className="btn-watch" onClick={() => handleOpenPlayer(m)}>Xem phim</button>
                          <button className="btn-secondary" onClick={() => { setRatingModalMovie(m); setRatingScore(9.0); }}>Đánh giá</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Thanh lọc theo Thể loại */}
            <div className="genre-bar-container">
              <div className="genre-bar-title">Lọc theo thể loại:</div>
              <div className="genre-bar">
                <button
                  className={`genre-pill ${selectedGenre === 'All' ? 'active' : ''}`}
                  onClick={() => { setSelectedGenre('All'); fetchMovies('All', searchQuery); }}
                >
                  Tất cả
                </button>
                {genres.map((g) => (
                  <button
                    key={g.name}
                    className={`genre-pill ${selectedGenre === g.name ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedGenre(g.name);
                      fetchMovies(g.name, searchQuery);
                    }}
                  >
                    {g.name} ({g.count})
                  </button>
                ))}
              </div>
            </div>

            <h2 className="section-title">
              {searchMode === 'plot' && plotQuery
                ? `Phim có cốt truyện khớp nhất với: "${plotQuery}"`
                : selectedGenre !== 'All'
                ? `Danh sách phim thể loại: ${selectedGenre}`
                : `Danh sách phim thịnh hành`}
            </h2>

            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>Đang tải dữ liệu phim...</div>
            ) : (
              <div className="movie-grid">
                {movies.map((m) => (
                  <div key={m.id} className="movie-card">
                    <div className="poster-wrap">
                      <img src={m.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'} alt={m.title} className="movie-poster" />
                      <span className="rating-badge">Điểm: {m.rating || 'N/A'}</span>
                      {m.similarity_score && (
                        <span className="similarity-badge">Khớp {(m.similarity_score * 100).toFixed(0)}%</span>
                      )}
                    </div>
                    <div className="movie-info">
                      <h3 className="movie-title">{m.title}</h3>
                      <div className="movie-meta">{m.year} • {m.runtime_minutes ? `${m.runtime_minutes} phút` : ''}</div>
                      <div className="movie-genres">{m.genres}</div>
                      {m.recommendation_reason && (
                        <div className="recommendation-reason">{m.recommendation_reason}</div>
                      )}
                      <div className="card-actions">
                        <button className="btn-watch" onClick={() => handleOpenPlayer(m)}>Xem phim</button>
                        <button className="btn-secondary" onClick={() => { setRatingModalMovie(m); setRatingScore(9.0); }}>Đánh giá</button>
                        <button className="btn-recommend" onClick={() => handleGetRecommendations(m.title)}>Gợi ý tương tự</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Tab 2: Dành Cho Bạn (Cá Nhân Hóa) */}
        {tab === 'for_you' && (
          <>
            <h2 className="section-title">Danh sách phim gợi ý dành riêng cho bạn ({user ? user.username : ''})</h2>
            <p style={{ color: '#9ca3af', fontSize: '14px', marginBottom: '24px' }}>
              {personalizedMsg || 'Hệ thống phân tích các thể loại và đặc trưng từ những bộ phim bạn đã xem và đánh giá cao để đề xuất danh sách này.'}
            </p>
            {personalizedMovies.length === 0 ? (
              <p style={{ color: '#9ca3af' }}>Bạn chưa xem hoặc đánh giá phim nào. Hãy bấm "Xem phim" hoặc "Đánh giá" để hệ thống học gu xem phim của bạn.</p>
            ) : (
              <div className="movie-grid">
                {personalizedMovies.map((m) => (
                  <div key={m.id} className="movie-card">
                    <div className="poster-wrap">
                      <img src={m.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'} alt={m.title} className="movie-poster" />
                      <span className="rating-badge">Điểm: {m.rating || 'N/A'}</span>
                      <span className="similarity-badge">Gu của bạn</span>
                    </div>
                    <div className="movie-info">
                      <h3 className="movie-title">{m.title}</h3>
                      <div className="movie-meta">{m.year} • {m.runtime_minutes ? `${m.runtime_minutes} phút` : ''}</div>
                      <div className="movie-genres">{m.genres}</div>
                      {m.recommendation_reason && (
                        <div className="recommendation-reason">{m.recommendation_reason}</div>
                      )}
                      <div className="card-actions">
                        <button className="btn-watch" onClick={() => handleOpenPlayer(m)}>Xem phim</button>
                        <button className="btn-secondary" onClick={() => { setRatingModalMovie(m); setRatingScore(9.0); }}>Đánh giá</button>
                        <button className="btn-recommend" onClick={() => handleGetRecommendations(m.title)}>Gợi ý tương tự</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Tab 3: Gợi ý tương đồng */}
        {tab === 'recommend' && (
          <>
            <div className="search-box" style={{ marginBottom: '24px' }}>
              <input
                className="search-input"
                type="text"
                placeholder="Nhập tên phim gốc bạn thích (ví dụ: Interstellar, Inception, The Dark Knight)..."
                value={recommendQuery}
                onChange={(e) => setRecommendQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleGetRecommendations(recommendQuery)}
              />
              <button className="btn-recommend" onClick={() => handleGetRecommendations(recommendQuery)}>Gợi ý ngay</button>
            </div>
            
            <h2 className="section-title">Kết quả gợi ý tương đồng {recommendQuery ? `cho: "${recommendQuery}"` : ''}</h2>
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>Đang tính toán độ tương đồng nội dung...</div>
            ) : (
              <div className="movie-grid">
                {recommendations.map((m) => (
                  <div key={m.id} className="movie-card">
                    <div className="poster-wrap">
                      <img src={m.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'} alt={m.title} className="movie-poster" />
                      <span className="rating-badge">Điểm: {m.rating}</span>
                      <span className="similarity-badge">{(m.similarity_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="movie-info">
                      <h3 className="movie-title">{m.title}</h3>
                      <div className="movie-meta">{m.year} • {m.runtime_minutes ? `${m.runtime_minutes} phút` : ''}</div>
                      <div className="movie-genres">{m.genres}</div>
                      {m.recommendation_reason && (
                        <div className="recommendation-reason">{m.recommendation_reason}</div>
                      )}
                      <div className="card-actions">
                        <button className="btn-watch" onClick={() => handleOpenPlayer(m)}>Xem phim</button>
                        <button className="btn-secondary" onClick={() => { setRatingModalMovie(m); setRatingScore(9.0); }}>Đánh giá</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Tab 4: Lịch sử xem phim */}
        {tab === 'history' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 className="section-title" style={{ marginBottom: 0 }}>Lịch sử xem phim của bạn</h2>
              {history.length > 0 && (
                <button className="btn-clear-all" onClick={handleClearAllHistory}>
                  Xóa toàn bộ lịch sử
                </button>
              )}
            </div>
            {history.length === 0 ? (
              <p style={{ color: '#9ca3af' }}>Bạn chưa có lịch sử xem phim nào. Bấm "Xem phim" ở bất kỳ bộ phim nào để trải nghiệm.</p>
            ) : (
              <div className="movie-grid">
                {history.map((h) => (
                  <div key={h.id} className="movie-card">
                    <div className="poster-wrap">
                      <img src={h.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'} alt={h.movie_title} className="movie-poster" />
                    </div>
                    <div className="movie-info">
                      <h3 className="movie-title">{h.movie_title}</h3>
                      <div className="movie-meta">Đã xem: {new Date(h.watched_at).toLocaleString('vi-VN')}</div>
                      <div className="card-actions" style={{ flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn-watch" style={{ flex: 1 }} onClick={() => handleOpenPlayer({ id: h.movie_id, title: h.movie_title, poster_url: h.poster_url })}>
                            Xem lại
                          </button>
                          <button className="btn-recommend" style={{ flex: 1 }} onClick={() => handleGetRecommendations(h.movie_title)}>
                            Gợi ý tương tự
                          </button>
                        </div>
                        <button className="btn-delete" style={{ width: '100%' }} onClick={() => handleDeleteSingleHistory(h.movie_id, h.movie_title)}>
                          Xóa khỏi lịch sử
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Tab 5: Đánh giá của tôi */}
        {tab === 'ratings' && (
          <>
            <h2 className="section-title">Danh sách phim bạn đã đánh giá</h2>
            {ratings.length === 0 ? (
              <p style={{ color: '#9ca3af' }}>Bạn chưa đánh giá bộ phim nào.</p>
            ) : (
              <div className="movie-grid">
                {ratings.map((r) => (
                  <div key={r.id} className="movie-card">
                    <div className="poster-wrap">
                      <img src={r.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'} alt={r.movie_title} className="movie-poster" />
                      <span className="rating-badge">Điểm: {r.score}/10</span>
                    </div>
                    <div className="movie-info">
                      <h3 className="movie-title">{r.movie_title}</h3>
                      <div className="movie-meta">Đánh giá lúc: {new Date(r.updated_at).toLocaleDateString('vi-VN')}</div>
                      {r.comment && <p style={{ fontSize: '13px', color: '#d1d5db', fontStyle: 'italic', margin: '8px 0' }}>"{r.comment}"</p>}
                      <div className="card-actions" style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                        <button className="btn-recommend" style={{ flex: 2 }} onClick={() => handleGetRecommendations(r.movie_title)}>
                          Gợi ý tương tự
                        </button>
                        <button className="btn-delete" style={{ flex: 1 }} onClick={() => handleDeleteRating(r.movie_id, r.movie_title)}>
                          Xóa đánh giá
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Cửa sổ Modal trình phát phim & trailer */}
      {playerMovie && (
        <div className="modal-overlay" onClick={() => setPlayerMovie(null)}>
          <div className="player-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="player-header">
              <h3 className="player-title">{playerMovie.title} ({playerMovie.year || '2024'})</h3>
              <button className="btn-secondary" style={{ padding: '6px 12px' }} onClick={() => setPlayerMovie(null)}>Đóng</button>
            </div>

            {/* Các tab chuyển đổi nguồn phát phim */}
            <div className="player-tabs" style={{ flexWrap: 'wrap', gap: '8px' }}>
              <button
                className={`player-tab-btn ${playerSource === 'twoembed' ? 'active' : ''}`}
                onClick={() => setPlayerSource('twoembed')}
              >
                Máy chủ 1 (2Embed)
              </button>
              <button
                className={`player-tab-btn ${playerSource === 'twoembed_skin' ? 'active' : ''}`}
                onClick={() => setPlayerSource('twoembed_skin')}
              >
                Máy chủ 2 (2Embed dự phòng)
              </button>
              <button
                className={`player-tab-btn ${playerSource === 'multiembed' ? 'active' : ''}`}
                onClick={() => setPlayerSource('multiembed')}
              >
                Máy chủ 3 (MultiEmbed)
              </button>
              <button
                className={`player-tab-btn ${playerSource === 'sample' ? 'active' : ''}`}
                onClick={() => setPlayerSource('sample')}
              >
                Bản chiếu thử Full HD
              </button>
              <a
                href={`https://www.youtube.com/results?search_query=${encodeURIComponent(playerMovie.title)}+official+trailer`}
                target="_blank"
                rel="noreferrer"
                className="player-tab-btn"
                style={{ textDecoration: 'none', background: '#dc2626', color: '#fff', marginLeft: 'auto' }}
              >
                Mở Trailer trên YouTube
              </a>
              <a
                href={playerMovie.imdb_url || `https://www.imdb.com/title/${playerMovie.id}/`}
                target="_blank"
                rel="noreferrer"
                className="player-tab-btn"
                style={{ textDecoration: 'none' }}
              >
                Trang IMDb gốc
              </a>
            </div>

            {/* Khung phát video tùy theo nguồn */}
            {playerSource === 'sample' ? (
              <video
                className="video-player-frame"
                controls
                autoPlay
                src="https://vjs.zencdn.net/v/oceans.mp4"
                poster={playerMovie.poster_url}
              >
                Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
              </video>
            ) : (
              <iframe
                key={playerSource}
                className="video-player-frame"
                src={
                  playerSource === 'twoembed'
                    ? `https://2embed.cc/embed/${playerMovie.id}`
                    : playerSource === 'twoembed_skin'
                    ? `https://www.2embed.skin/embed/${playerMovie.id}`
                    : `https://multiembed.mov/?video_id=${playerMovie.id}`
                }
                title={`Movie Player - ${playerMovie.title}`}
                allowFullScreen
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              ></iframe>
            )}

            <div style={{ marginTop: '14px', fontSize: '13px', background: '#0f121d', padding: '12px 16px', borderRadius: '8px', border: '1px solid #23283b', lineHeight: '1.6' }}>
              <div style={{ color: '#10b981', fontWeight: 600, marginBottom: '4px' }}>
                Lưu ý khi xem phim:
              </div>
              <div style={{ color: '#9ca3af' }}>
                • <strong style={{ color: '#fff' }}>Máy chủ 1 và Máy chủ 2 (2Embed):</strong> Đang chạy ổn định trên toàn bộ kho phim IMDb, hỗ trợ nhiều luồng stream phụ.<br />
                • <strong style={{ color: '#fff' }}>Máy chủ 3 (MultiEmbed):</strong> Nguồn stream quốc tế dự phòng.<br />
                • <strong style={{ color: '#fff' }}>Chặn cửa sổ quảng cáo (Pop-up):</strong> Khuyến nghị sử dụng trình duyệt Brave hoặc tiện ích uBlock Origin để loại bỏ các tab quảng cáo khi bấm phát phim.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cửa sổ Modal Đăng nhập / Đăng ký */}
      {showAuthModal && (
        <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{isRegister ? 'Đăng ký tài khoản' : 'Đăng nhập'}</h3>
            {authError && <div style={{ color: '#ef4444', marginBottom: '14px', fontSize: '13px' }}>{authError}</div>}
            <form onSubmit={handleAuthSubmit}>
              <div className="form-group">
                <label>Tên đăng nhập</label>
                <input
                  className="form-input"
                  type="text"
                  required
                  value={authForm.username}
                  onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
                />
              </div>
              {isRegister && (
                <div className="form-group">
                  <label>Email</label>
                  <input
                    className="form-input"
                    type="email"
                    required
                    value={authForm.email}
                    onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                  />
                </div>
              )}
              <div className="form-group">
                <label>Mật khẩu</label>
                <input
                  className="form-input"
                  type="password"
                  required
                  value={authForm.password}
                  onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>{isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}</button>
                <button type="button" className="btn-secondary" onClick={() => setIsRegister(!isRegister)}>
                  {isRegister ? 'Đã có tài khoản?' : 'Đăng ký mới'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Cửa sổ Modal Đánh giá phim */}
      {ratingModalMovie && (
        <div className="modal-overlay" onClick={() => setRatingModalMovie(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Đánh giá: {ratingModalMovie.title}</h3>
            <div className="form-group">
              <label>Điểm số (Thang 1.0 - 10.0)</label>
              <input
                className="form-input"
                type="number"
                step="0.5"
                min="1.0"
                max="10.0"
                value={ratingScore}
                onChange={(e) => setRatingScore(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Cảm nhận / Bình luận (tùy chọn)</label>
              <textarea
                className="form-input"
                rows="3"
                value={ratingComment}
                onChange={(e) => setRatingComment(e.target.value)}
                placeholder="Cảm nhận của bạn về bộ phim..."
              ></textarea>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button className="btn-primary" style={{ flex: 1 }} onClick={handleSubmitRating}>Gửi đánh giá</button>
              <button className="btn-secondary" onClick={() => setRatingModalMovie(null)}>Hủy</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
