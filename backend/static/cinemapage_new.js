function CinemaPage({ navigate }) {
  const { user } = useAuth();
  const { t } = useLang();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('movies');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState('');
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [voiceTracks, setVoiceTracks] = useState([]);
  const [activeTrack, setActiveTrack] = useState(null);
  const [streamsLoading, setStreamsLoading] = useState(false);

  if (!user || !user.is_admin) return <div className="container" style={{paddingTop:100}}><div className="empty-state"><div className="empty-icon"><i className="ri-shield-star-line"></i></div><h3>{t('adminRequired')}</h3><button className="btn btn-primary" onClick={()=>navigate('/')} style={{marginTop:16}}>{t('goHome')}</button></div></div>;

  const loadMovies = (pg = 1) => {
    setLoading(true);
    api.get(`/api/hdrezka/browse?category=films&page=${pg}`)
      .then(d => setItems(pg === 1 ? d : [...items, ...d]))
      .catch(() => toast.addToast('Failed to load', 'error'))
      .finally(() => setLoading(false));
  };

  const loadAnime = (pg = 1) => {
    setLoading(true);
    api.get(`/api/anilibria/browse?page=${pg}&limit=20`)
      .then(d => setItems(pg === 1 ? d : [...items, ...d]))
      .catch(() => toast.addToast('Failed to load anime', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (activeTab === 'movies') loadMovies(page);
    else loadAnime(page);
  }, [activeTab, page]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    const endpoint = activeTab === 'movies'
      ? `/api/hdrezka/search?q=${encodeURIComponent(query.trim())}`
      : `/api/anilibria/search?q=${encodeURIComponent(query.trim())}`;
    api.get(endpoint).then(d => setItems(d)).catch(() => toast.addToast('Search failed', 'error')).finally(() => setLoading(false));
  };

  const openDetail = (item) => {
    setDetailLoading(true);
    setDetail(null);
    setVoiceTracks([]);
    setActiveTrack(null);
    setStreamsLoading(false);
    const endpoint = activeTab === 'movies'
      ? `/api/hdrezka/detail?url=${encodeURIComponent(item.url || item.link)}`
      : `/api/anilibria/detail?code=${encodeURIComponent(item.code)}`;
    api.get(endpoint).then(d => {
      setDetail(d);
      if (activeTab === 'movies' && d.player_url) {
        setStreamsLoading(true);
        api.get('/api/hdrezka/streams?embed_url=' + encodeURIComponent(d.player_url))
          .then(r => { if (r.tracks?.length > 0) { setVoiceTracks(r.tracks); setActiveTrack(r.tracks[0]); } })
          .catch(() => {}).finally(() => setStreamsLoading(false));
      }
    }).catch(() => toast.addToast('Failed to load details', 'error')).finally(() => setDetailLoading(false));
  };

  const goBack = () => { setDetail(null); setVoiceTracks([]); setActiveTrack(null); setStreamsLoading(false); };

  if (detail) {
    return (
      <div className="container" style={{paddingTop:80}}>
        <button className="btn-back" onClick={goBack} style={{marginBottom:20}}><i className="ri-arrow-left-line"></i> {t('back')}</button>
        {detailLoading ? <div className="loader"><div className="spinner"></div></div> : detail && (
          <div className="cinema-detail">
            <div className="cinema-poster">{detail.poster && <ProgressiveImg src={detail.poster} alt={detail.title} />}</div>
            <div className="cinema-info">
              <h2>{detail.title}</h2>
              {detail.title_en && <div className="original-title">{detail.title_en}</div>}
              <div className="cinema-meta">
                {detail.rating > 0 && <span className="cinema-meta-badge rating"><i className="ri-star-fill"></i> {detail.rating.toFixed(1)}</span>}
                {detail.year && <span className="cinema-meta-badge"><i className="ri-calendar-line"></i> {detail.year}</span>}
                {detail.type && <span className="cinema-meta-badge"><i className="ri-film-line"></i> {detail.type}</span>}
                {detail.status && <span className="cinema-meta-badge"><i className="ri-check-line"></i> {detail.status === 'ongoing' ? 'Онгоинг' : 'Завершён'}</span>}
                {detail.episodes_count > 0 && <span className="cinema-meta-badge"><i className="ri-list-check"></i> {detail.episodes_count} эп.</span>}
              </div>
              {detail.genres?.length > 0 && <div className="cinema-genres">{detail.genres.map((g,i) => <span key={i} className="cinema-genre-tag">{g}</span>)}</div>}
              {detail.description && <div className="cinema-description">{detail.description}</div>}
              {activeTab === 'movies' && (
                <div className="cinema-player-section">
                  <div className="cinema-player-header"><i className="ri-play-circle-fill"></i> Плеер</div>
                  {voiceTracks.length > 1 && <div className="cinema-translator-select">{voiceTracks.map(tr => (<button key={tr.voice_id} className={`cinema-translator-btn ${activeTrack?.voice_id === tr.voice_id ? 'active' : ''}`} onClick={() => setActiveTrack(tr)}><i className="ri-translate-2"></i> {tr.title}</button>))}</div>}
                  {streamsLoading ? <div className="cinema-player"><div className="cinema-loading-player"><div className="spinner"></div></div></div> : activeTrack ? <CinemaPlayer key={activeTrack.voice_id} hlsUrl={activeTrack.hls_url} /> : detail.player_url ? <div className="cinema-no-player"><div className="cinema-no-player-icon"><i className="ri-loader-4-line"></i></div><p>Загрузка...</p></div> : <div className="cinema-no-player"><div className="cinema-no-player-icon"><i className="ri-movie-2-line"></i></div><p>Плеер недоступен</p></div>}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="container" style={{paddingTop:80}}>
      <div className="page-header">
        <h1><i className="ri-film-line" style={{marginRight:12,color:'var(--accent-primary)'}}></i>Cinema</h1>
        <p style={{color:'var(--text-muted)',marginTop:4}}>HDRezka + AniLibria — Администрирование</p>
      </div>
      <div className="cinema-tabs" style={{marginBottom:20}}>
        <button className={`cinema-tab ${activeTab === 'movies' ? 'active' : ''}`} onClick={() => {setActiveTab('movies');setPage(1);setItems([]);setQuery('');}}><i className="ri-movie-2-line"></i> Кино (HDRezka)</button>
        <button className={`cinema-tab ${activeTab === 'anime' ? 'active' : ''}`} onClick={() => {setActiveTab('anime');setPage(1);setItems([]);setQuery('');}}><i className="ri-robot-2-line"></i> Аниме (AniLibria)</button>
      </div>
      <form onSubmit={handleSearch} style={{display:'flex',gap:8,marginBottom:20}}>
        <input className="input" style={{flex:1}} placeholder={activeTab === 'anime' ? 'Поиск аниме...' : 'Поиск фильмов...'} value={query} onChange={e => setQuery(e.target.value)} />
        <button className="btn btn-primary" type="submit"><i className="ri-search-line"></i> Поиск</button>
      </form>
      {loading && items.length === 0 ? <div className="loader"><div className="spinner"></div></div> : (
        <>
          <div className="cinema-grid">{items.map((item, i) => (<div key={(item.id||item.code||'')+'-'+i} className="cinema-card" onClick={() => openDetail(item)}>{item.poster || item.image ? <img className="cinema-card-img" src={item.poster || item.image} alt={item.title} loading="lazy" /> : <div className="cinema-card-img" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><i className="ri-film-line" style={{fontSize:'2rem',color:'var(--text-muted)'}}></i></div>}<div className="cinema-card-body"><div className="cinema-card-title">{item.title}</div>{item.year && <div className="cinema-card-type">{item.year} • {item.type || ''}</div>}</div></div>))}</div>
          {items.length === 0 && !loading && <div className="empty-state"><div className="empty-icon"><i className="ri-film-line"></i></div><h3>Нет результатов</h3></div>}
          {items.length > 0 && <div style={{textAlign:'center',marginTop:24}}><button className="btn btn-secondary" onClick={() => setPage(p => p + 1)} disabled={loading}>{loading ? <><div className="spinner" style={{width:16,height:16}}></div> Загрузка...</> : <><i className="ri-arrow-down-line"></i> Ещё</>}</button></div>}
        </>
      )}
    </div>
  );
}
