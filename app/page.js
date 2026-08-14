'use client'

import { useState, useEffect, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { toast } from 'sonner'
import {
  Package, Truck, Building2, MapPin, User, Users, Plus, Search, Filter,
  Send, CheckCircle2, Clock, AlertCircle, PackageCheck, LayoutDashboard,
  Trash2, Edit, ArrowLeft, Phone, Calendar, MessageCircle, X
} from 'lucide-react'

const SHIPMENT_TYPES = {
  ic_nakliye: 'İç Nakliye',
  musteri_kendisi: 'Müşteri Kendisi Gönderecek',
  musteri_kargo: 'Müşteri Kargolayacak',
  nakliyeci: 'Nakliyeci Firma',
}

const STATUS_LABELS = {
  created: 'Oluşturuldu',
  planning: 'Planlama Bekliyor',
  planned: 'Planlandı',
  in_transit: 'Yolda',
  delivered: 'Depoya Ulaştı',
  shipped: 'Gönderildi',
  cancelled: 'İptal',
}

const STATUS_COLORS = {
  created: 'bg-slate-200 text-slate-800',
  planning: 'bg-amber-100 text-amber-800 border border-amber-300',
  planned: 'bg-blue-100 text-blue-800 border border-blue-300',
  in_transit: 'bg-indigo-100 text-indigo-800 border border-indigo-300',
  delivered: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
  shipped: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
  cancelled: 'bg-rose-100 text-rose-800 border border-rose-300',
}

const TOKEN_KEY = 'yuktakip_token'

const getToken = () => (typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null)
const setToken = (t) => { if (typeof window !== 'undefined') { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY) } }

// Global logout hook set by App to clear session on 401
let onUnauthorized = null

const api = async (path, opts = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token
  const res = await fetch('/api/' + path, { ...opts, headers })
  if (res.status === 401) {
    if (onUnauthorized) onUnauthorized()
    const e = await res.json().catch(() => ({ error: 'Yetkisiz' }))
    throw new Error(e.error || 'Yetkisiz')
  }
  if (!res.ok) {
    const e = await res.json().catch(() => ({ error: 'İstek hatası' }))
    throw new Error(e.error || 'Hata')
  }
  return res.json()
}

// Role constants (must match backend)
const ROLE = { YS: 'yuk_sorumlusu', AP: 'arac_planlama', DP: 'depocu' }
const ROLE_LABELS = { yuk_sorumlusu: 'Yük Sorumlusu', arac_planlama: 'Araç Planlama', depocu: 'Depocu' }
const hasRole = (user, r) => user && Array.isArray(user.roles) && user.roles.includes(r)
const hasAny = (user, arr) => arr.some(r => hasRole(user, r))

function App() {
  const [user, setUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)

  // Check existing session on mount
  useEffect(() => {
    onUnauthorized = () => { setToken(null); setUser(null) }
    const token = getToken()
    if (!token) { setAuthChecked(true); return }
    api('auth/me').then(u => { setUser(u); setAuthChecked(true) }).catch(() => { setToken(null); setAuthChecked(true) })
  }, [])

  const handleLogin = (token, u) => {
    setToken(token)
    setUser(u)
  }

  const handleLogout = async () => {
    try { await api('auth/logout', { method: 'POST' }) } catch (e) {}
    setToken(null)
    setUser(null)
  }

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-500">Yükleniyor...</div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />
  }

  return <MainApp user={user} onLogout={handleLogout} />
}

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [demoUsers, setDemoUsers] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api('auth/init', { method: 'POST' }).then(d => setDemoUsers(d.demoUsers || [])).catch(() => {})
  }, [])

  const doLogin = async (u, p) => {
    setLoading(true)
    try {
      const res = await api('auth/login', { method: 'POST', body: JSON.stringify({ username: u, password: p }) })
      onLogin(res.token, res.user)
      toast.success('Hoş geldin, ' + res.user.name)
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg">
            <Truck className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold mt-3">YükTakip</h1>
          <p className="text-slate-500 text-sm">Lojistik Operasyon Paneli</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Giriş Yap</CardTitle>
            <CardDescription>Operasyon rolünüzle giriş yapın</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Kullanıcı Adı</Label>
              <Input value={username} onChange={e => setUsername(e.target.value)} onKeyDown={e => e.key === 'Enter' && doLogin(username, password)} />
            </div>
            <div>
              <Label>Şifre</Label>
              <Input type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && doLogin(username, password)} />
            </div>
            <Button className="w-full" disabled={loading || !username || !password} onClick={() => doLogin(username, password)}>
              {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
            </Button>

            {demoUsers.length > 0 && (
              <>
                <div className="relative py-2">
                  <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-slate-200" /></div>
                  <div className="relative flex justify-center text-xs uppercase"><span className="bg-white px-2 text-slate-500">Demo Kullanıcıları</span></div>
                </div>
                <div className="grid gap-2">
                  {demoUsers.map(du => {
                    const role = du.roles?.[0]
                    const colors = { yuk_sorumlusu: 'from-blue-500 to-indigo-500', arac_planlama: 'from-amber-500 to-orange-500', depocu: 'from-emerald-500 to-green-500' }
                    const icons = { yuk_sorumlusu: Package, arac_planlama: Truck, depocu: PackageCheck }
                    const I = icons[role] || User
                    return (
                      <button key={du.username} onClick={() => doLogin(du.username, du.password)} disabled={loading}
                        className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-slate-50 transition text-left">
                        <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${colors[role] || 'from-slate-500 to-slate-600'} flex items-center justify-center text-white flex-shrink-0`}>
                          <I className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{ROLE_LABELS[role] || role}</p>
                          <p className="text-xs text-slate-500">{du.username} / {du.password}</p>
                        </div>
                        <ArrowLeft className="w-4 h-4 text-slate-400 rotate-180" />
                      </button>
                    )
                  })}
                </div>
              </>
            )}
          </CardContent>
        </Card>
        <p className="text-center text-xs text-slate-500 mt-4">YükTakip MVP · Rol tabanlı giriş</p>
      </div>
    </div>
  )
}

function MainApp({ user, onLogout }) {
  const [view, setView] = useState('dashboard')
  const [selectedLoadId, setSelectedLoadId] = useState(null)
  const [dashRecent, setDashRecent] = useState([])
  const [hasAnyLoads, setHasAnyLoads] = useState(false)
  const [companies, setCompanies] = useState([])
  const [addresses, setAddresses] = useState([])
  const [drivers, setDrivers] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [dashboard, setDashboard] = useState({ total: 0, pending: 0, planning: 0, planned: 0, delivered: 0 })

  // Compute which tabs user can see
  const availableTabs = useMemo(() => {
    const tabs = [
      { k: 'dashboard', l: 'Dashboard', I: LayoutDashboard, roles: [ROLE.YS, ROLE.AP, ROLE.DP] },
      { k: 'loads', l: 'Yükler', I: Package, roles: [ROLE.YS, ROLE.AP, ROLE.DP] },
      { k: 'companies', l: 'Firmalar', I: Building2, roles: [ROLE.YS] },
      { k: 'drivers', l: 'Şoförler', I: Users, roles: [ROLE.AP] },
      { k: 'vehicles', l: 'Araçlar', I: Truck, roles: [ROLE.AP, ROLE.DP] },
    ].filter(t => hasAny(user, t.roles))
    // vehicles for depocu is read-only, but they don't really need it. Restrict to arac_planlama only.
    return tabs.filter(t => !(t.k === 'vehicles' && !hasRole(user, ROLE.AP)))
  }, [user])

  const canView = (k) => availableTabs.some(t => t.k === k) || k === 'detail'

  const refreshAll = async () => {
    try {
      const canGetCompanies = true // read for all
      const canGetDrivers = hasAny(user, [ROLE.YS, ROLE.AP])
      const [recent, c, a, d, v, dash] = await Promise.all([
        api('loads?page=1&pageSize=6'),
        canGetCompanies ? api('companies') : Promise.resolve([]),
        canGetCompanies ? api('addresses') : Promise.resolve([]),
        canGetDrivers ? api('drivers') : Promise.resolve([]),
        api('vehicles'),
        api('dashboard'),
      ])
      setDashRecent(recent.items || [])
      setHasAnyLoads((recent.total || 0) > 0)
      setCompanies(c); setAddresses(a); setDrivers(d); setVehicles(v); setDashboard(dash)
    } catch (e) { toast.error(e.message) }
  }

  useEffect(() => { refreshAll() }, [])

  const [selectedLoad, setSelectedLoad] = useState(null)

  useEffect(() => {
    if (!selectedLoadId) { setSelectedLoad(null); return }
    let alive = true
    api(`loads/${selectedLoadId}`).then(d => { if (alive) setSelectedLoad(d) }).catch(e => toast.error(e.message))
    return () => { alive = false }
  }, [selectedLoadId])

  const refreshSelected = async () => {
    if (!selectedLoadId) return
    try { const d = await api(`loads/${selectedLoadId}`); setSelectedLoad(d) } catch (e) { toast.error(e.message) }
  }

  // If current view no longer accessible, redirect to dashboard
  useEffect(() => {
    if (!canView(view)) setView('dashboard')
  }, [view, availableTabs])


  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">YükTakip</h1>
              <p className="text-xs text-slate-500 leading-tight">Lojistik Operasyon Paneli</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 mr-2 px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center">
                <User className="w-3.5 h-3.5" />
              </div>
              <div className="text-xs leading-tight">
                <p className="font-medium">{user.name}</p>
                <p className="text-slate-500">{(user.roles || []).map(r => ROLE_LABELS[r] || r).join(', ')}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={onLogout} className="gap-1">
              <X className="w-3.5 h-3.5" />Çıkış
            </Button>
          </div>
        </div>
      </header>

      {/* Nav */}
      <nav className="bg-white border-b border-slate-200 sticky top-[65px] z-20">
        <div className="container mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto">
            {availableTabs.map(({ k, l, I }) => (
              <button key={k} onClick={() => { setView(k); setSelectedLoadId(null) }}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                  view === k ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}>
                <I className="w-4 h-4" />{l}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="flex-1 container mx-auto px-4 py-6">
        {view === 'dashboard' && canView('dashboard') && (
          <Dashboard dashboard={dashboard} loads={dashRecent} companies={companies} user={user} onOpenLoad={(id) => { setSelectedLoadId(id); setView('detail') }} onGoto={setView} />
        )}
        {view === 'loads' && !selectedLoadId && canView('loads') && (
          <LoadsView companies={companies} addresses={addresses} user={user}
            onOpen={(id) => { setSelectedLoadId(id); setView('detail') }}
            onDataChanged={refreshAll} />
        )}
        {view === 'detail' && selectedLoad && (
          <LoadDetail load={selectedLoad} companies={companies} addresses={addresses} drivers={drivers} vehicles={vehicles} user={user}
            onBack={() => { setView('loads'); setSelectedLoadId(null) }} onRefresh={() => { refreshAll(); refreshSelected() }} />
        )}
        {view === 'companies' && canView('companies') && (
          <CompaniesView companies={companies} addresses={addresses} onRefresh={refreshAll} />
        )}
        {view === 'drivers' && canView('drivers') && (
          <DriversView drivers={drivers} onRefresh={refreshAll} />
        )}
        {view === 'vehicles' && canView('vehicles') && (
          <VehiclesView vehicles={vehicles} onRefresh={refreshAll} />
        )}
        {!canView(view) && (
          <div className="text-center py-16">
            <AlertCircle className="w-12 h-12 mx-auto text-slate-300 mb-2" />
            <p className="text-slate-500">Bu ekrana erişim yetkiniz yok.</p>
            <Button className="mt-3" onClick={() => setView('dashboard')}>Dashboard'a Dön</Button>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-3 text-center text-xs text-slate-500">
        YükTakip MVP · Yükleri hızlı topla, hızlı planla
      </footer>
    </div>
  )
}

// ============ DASHBOARD ============
function Dashboard({ dashboard, loads, companies, onOpenLoad, onGoto }) {
  const stats = [
    { key: 'total', label: 'Toplam Yük', value: dashboard.total, color: 'from-slate-500 to-slate-700', I: Package },
    { key: 'pending', label: 'Bekleyen', value: dashboard.pending, color: 'from-slate-400 to-slate-500', I: Clock },
    { key: 'planning', label: 'Planlama Bekleyen', value: dashboard.planning, color: 'from-amber-500 to-orange-500', I: AlertCircle },
    { key: 'planned', label: 'Planlanan', value: dashboard.planned, color: 'from-blue-500 to-indigo-600', I: Truck },
    { key: 'delivered', label: 'Depoya Ulaşan', value: dashboard.delivered, color: 'from-emerald-500 to-green-600', I: PackageCheck },
  ]
  const recent = loads.slice(0, 6)
  const companyName = (id) => companies.find(c => c.id === id)?.name || '-'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Operasyon Özeti</h2>
        <p className="text-slate-500 text-sm mt-1">Yüklerin genel durumuna hızlı bakış</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {stats.map(s => (
          <Card key={s.key} className="overflow-hidden border-slate-200 hover:shadow-md transition-shadow cursor-pointer" onClick={() => onGoto('loads')}>
            <div className={`h-1 bg-gradient-to-r ${s.color}`} />
            <CardContent className="pt-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-slate-500 font-medium">{s.label}</p>
                  <p className="text-3xl font-bold mt-1">{s.value}</p>
                </div>
                <s.I className="w-5 h-5 text-slate-400" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Son Yükler</CardTitle>
              <CardDescription>En son oluşturulan yükler</CardDescription>
            </div>
            <Button size="sm" onClick={() => onGoto('loads')}>Tümünü Gör</Button>
          </div>
        </CardHeader>
        <CardContent>
          {recent.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Package className="w-12 h-12 mx-auto mb-2 text-slate-300" />
              <p>Henüz yük yok</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recent.map(l => (
                <div key={l.id} onClick={() => onOpenLoad(l.id)}
                  className="flex items-center justify-between p-3 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                      <Package className="w-5 h-5 text-slate-600" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium truncate">{companyName(l.companyId)}</p>
                      <p className="text-xs text-slate-500 truncate">{l.destCity} {l.destCountry && `· ${l.destCountry}`} · {SHIPMENT_TYPES[l.shipmentType]}</p>
                    </div>
                  </div>
                  <Badge className={STATUS_COLORS[l.status] + ' ml-2 flex-shrink-0'}>{STATUS_LABELS[l.status]}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ============ LOADS LIST ============
function LoadsView({ companies, addresses, onOpen, onDataChanged, user }) {
  const canCreate = hasRole(user, ROLE.YS)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [dateFilter, setDateFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState('all')
  const [shipmentFilter, setShipmentFilter] = useState('all')
  const [openCreate, setOpenCreate] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [debouncedSearch, setDebouncedSearch] = useState('')

  // Debounce search input
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 350)
    return () => clearTimeout(t)
  }, [search])

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, statusFilter, dateFilter, companyFilter, shipmentFilter, pageSize])

  const fetchLoads = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
      if (statusFilter !== 'all') params.set('status', statusFilter)
      if (companyFilter !== 'all') params.set('companyId', companyFilter)
      if (shipmentFilter !== 'all') params.set('shipmentType', shipmentFilter)
      if (dateFilter) params.set('date', dateFilter)
      if (debouncedSearch) params.set('q', debouncedSearch)
      const data = await api('loads?' + params.toString())
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  useEffect(() => { fetchLoads() }, [page, pageSize, statusFilter, companyFilter, shipmentFilter, dateFilter, debouncedSearch])

  const companyName = (id) => companies.find(c => c.id === id)?.name || '-'
  const addressCity = (id) => addresses.find(a => a.id === id)?.city || '-'

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(total, page * pageSize)

  const goPage = (p) => setPage(Math.min(totalPages, Math.max(1, p)))

  const pageNumbers = useMemo(() => {
    // Compact pagination: first, last, current +- 1
    const set = new Set([1, totalPages, page, page - 1, page + 1])
    return Array.from(set).filter(n => n >= 1 && n <= totalPages).sort((a, b) => a - b)
  }, [page, totalPages])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <h2 className="text-2xl font-bold">Yükler</h2>
          <p className="text-slate-500 text-sm">
            {total === 0 ? '0 yük' : `${from}-${to} / ${total} yük`}
            {loading && <span className="ml-2 text-blue-600">Yükleniyor...</span>}
          </p>
        </div>
        <Dialog open={openCreate} onOpenChange={setOpenCreate}>
          {canCreate && (
            <DialogTrigger asChild>
              <Button className="gap-2"><Plus className="w-4 h-4" />Yeni Yük</Button>
            </DialogTrigger>
          )}
          <LoadCreateDialog companies={companies} addresses={addresses} onClose={() => setOpenCreate(false)} onCreated={() => { setOpenCreate(false); fetchLoads(); onDataChanged && onDataChanged() }} />
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
              <Input placeholder="Firma, şehir, ülke ara..." value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger><SelectValue placeholder="Durum" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tüm Durumlar</SelectItem>
                {Object.entries(STATUS_LABELS).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={companyFilter} onValueChange={setCompanyFilter}>
              <SelectTrigger><SelectValue placeholder="Firma" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tüm Firmalar</SelectItem>
                {companies.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={shipmentFilter} onValueChange={setShipmentFilter}>
              <SelectTrigger><SelectValue placeholder="Gönderim şekli" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tüm Gönderim Şekilleri</SelectItem>
                {Object.entries(SHIPMENT_TYPES).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
              </SelectContent>
            </Select>
            <Input type="date" value={dateFilter} onChange={e => setDateFilter(e.target.value)} />
          </div>
        </CardContent>
      </Card>

      {/* Table (desktop) / Cards (mobile) */}
      <Card>
        <CardContent className="p-0">
          {items.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Package className="w-12 h-12 mx-auto mb-2 text-slate-300" />
              <p>{loading ? 'Yükleniyor...' : 'Yük bulunamadı'}</p>
            </div>
          ) : (
            <>
              {/* Desktop table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr className="text-left text-xs text-slate-600 uppercase">
                      <th className="px-3 py-2">Tarih</th>
                      <th className="px-3 py-2">Firma</th>
                      <th className="px-3 py-2">Yükleme</th>
                      <th className="px-3 py-2">Gidiş</th>
                      <th className="px-3 py-2">Gönderim</th>
                      <th className="px-3 py-2">Kap</th>
                      <th className="px-3 py-2">Kg</th>
                      <th className="px-3 py-2">m³</th>
                      <th className="px-3 py-2">Durum</th>
                      <th className="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map(l => (
                      <tr key={l.id} onClick={() => onOpen(l.id)} className="hover:bg-slate-50 cursor-pointer">
                        <td className="px-3 py-2 whitespace-nowrap">{l.loadDate}</td>
                        <td className="px-3 py-2 font-medium">{companyName(l.companyId)}</td>
                        <td className="px-3 py-2">{addressCity(l.addressId)}</td>
                        <td className="px-3 py-2">{l.destCity} {l.destCountry && <span className="text-slate-400">/ {l.destCountry}</span>}</td>
                        <td className="px-3 py-2 text-xs">{SHIPMENT_TYPES[l.shipmentType]}</td>
                        <td className="px-3 py-2">{l.packages}</td>
                        <td className="px-3 py-2">{l.kg}</td>
                        <td className="px-3 py-2">{l.m3}</td>
                        <td className="px-3 py-2"><Badge className={STATUS_COLORS[l.status]}>{STATUS_LABELS[l.status]}</Badge></td>
                        <td className="px-3 py-2 text-right text-slate-400">→</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {/* Mobile cards */}
              <div className="md:hidden divide-y divide-slate-100">
                {items.map(l => (
                  <div key={l.id} onClick={() => onOpen(l.id)} className="p-4 hover:bg-slate-50 cursor-pointer">
                    <div className="flex justify-between items-start mb-1">
                      <p className="font-semibold">{companyName(l.companyId)}</p>
                      <Badge className={STATUS_COLORS[l.status] + ' text-xs'}>{STATUS_LABELS[l.status]}</Badge>
                    </div>
                    <p className="text-xs text-slate-500">{l.loadDate} · {addressCity(l.addressId)} → {l.destCity} {l.destCountry}</p>
                    <p className="text-xs text-slate-500 mt-1">{SHIPMENT_TYPES[l.shipmentType]} · {l.packages && `${l.packages} kap`} {l.kg && `· ${l.kg}kg`} {l.m3 && `· ${l.m3}m³`}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > 0 && (
        <Card>
          <CardContent className="py-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <span>Sayfa başına:</span>
                <Select value={String(pageSize)} onValueChange={v => setPageSize(parseInt(v, 10))}>
                  <SelectTrigger className="w-20 h-8"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="25">25</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="200">200</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="outline" size="sm" disabled={page === 1 || loading} onClick={() => goPage(page - 1)}>Önceki</Button>
                {pageNumbers.map((n, i) => {
                  const prev = pageNumbers[i - 1]
                  const gap = prev && n - prev > 1
                  return (
                    <span key={n} className="flex items-center">
                      {gap && <span className="px-1 text-slate-400">…</span>}
                      <Button variant={n === page ? 'default' : 'outline'} size="sm" onClick={() => goPage(n)} disabled={loading} className="min-w-[36px]">{n}</Button>
                    </span>
                  )
                })}
                <Button variant="outline" size="sm" disabled={page >= totalPages || loading} onClick={() => goPage(page + 1)}>Sonraki</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ============ LOAD CREATE DIALOG ============
function LoadCreateDialog({ companies, addresses, onClose, onCreated }) {
  const [form, setForm] = useState({
    loadDate: new Date().toISOString().substring(0, 10),
    companyId: '', addressId: '', phone: '', packages: '', kg: '', m3: '',
    dimensions: '', destCity: '', destCountry: 'Türkiye', shipmentType: 'ic_nakliye', note: '',
  })
  const [saving, setSaving] = useState(false)
  const companyAddresses = addresses.filter(a => a.companyId === form.companyId)

  const save = async () => {
    if (!form.companyId) return toast.error('Firma seçin')
    if (!form.addressId) return toast.error('Firma adresi seçin')
    setSaving(true)
    try {
      await api('loads', { method: 'POST', body: JSON.stringify(form) })
      toast.success('Yük oluşturuldu')
      onCreated()
    } catch (e) { toast.error(e.message) } finally { setSaving(false) }
  }

  return (
    <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Yeni Yük Oluştur</DialogTitle>
        <DialogDescription>Yük bilgilerini girin. Firma seçtikten sonra o firmaya ait adresler listelenir.</DialogDescription>
      </DialogHeader>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <Label>Yük Tarihi *</Label>
          <Input type="date" value={form.loadDate} onChange={e => setForm({ ...form, loadDate: e.target.value })} />
        </div>
        <div>
          <Label>Gönderim Şekli *</Label>
          <Select value={form.shipmentType} onValueChange={v => setForm({ ...form, shipmentType: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {Object.entries(SHIPMENT_TYPES).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Müşteri Firma *</Label>
          <Select value={form.companyId} onValueChange={v => setForm({ ...form, companyId: v, addressId: '' })}>
            <SelectTrigger><SelectValue placeholder="Firma seçin" /></SelectTrigger>
            <SelectContent>
              {companies.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Firma Adresi *</Label>
          <Select value={form.addressId} onValueChange={v => {
            const a = addresses.find(x => x.id === v)
            setForm({ ...form, addressId: v, phone: form.phone || a?.phone || '' })
          }} disabled={!form.companyId}>
            <SelectTrigger><SelectValue placeholder={form.companyId ? 'Adres seçin' : 'Önce firma seçin'} /></SelectTrigger>
            <SelectContent>
              {companyAddresses.map(a => <SelectItem key={a.id} value={a.id}>{a.name} · {a.city}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Telefon</Label>
          <Input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="05xx..." />
        </div>
        <div>
          <Label>Kap</Label>
          <Input value={form.packages} onChange={e => setForm({ ...form, packages: e.target.value })} placeholder="örn. 5" />
        </div>
        <div>
          <Label>Kg</Label>
          <Input value={form.kg} onChange={e => setForm({ ...form, kg: e.target.value })} placeholder="örn. 250" />
        </div>
        <div>
          <Label>m³</Label>
          <Input value={form.m3} onChange={e => setForm({ ...form, m3: e.target.value })} placeholder="örn. 1.5" />
        </div>
        <div className="md:col-span-2">
          <Label>Ölçüler</Label>
          <Input value={form.dimensions} onChange={e => setForm({ ...form, dimensions: e.target.value })} placeholder="örn. 120x80x100" />
        </div>
        <div>
          <Label>Gideceği Şehir</Label>
          <Input value={form.destCity} onChange={e => setForm({ ...form, destCity: e.target.value })} />
        </div>
        <div>
          <Label>Gideceği Ülke</Label>
          <Input value={form.destCountry} onChange={e => setForm({ ...form, destCountry: e.target.value })} />
        </div>
        <div className="md:col-span-2">
          <Label>Not</Label>
          <Textarea rows={3} value={form.note} onChange={e => setForm({ ...form, note: e.target.value })} />
        </div>
      </div>
      <DialogFooter className="gap-2">
        <Button variant="outline" onClick={onClose}>İptal</Button>
        <Button onClick={save} disabled={saving}>{saving ? 'Kaydediliyor...' : 'Yükü Oluştur'}</Button>
      </DialogFooter>
    </DialogContent>
  )
}

// ============ LOAD DETAIL ============
function LoadDetail({ load, companies, addresses, drivers, vehicles, user, onBack, onRefresh }) {
  const [planOpen, setPlanOpen] = useState(false)
  const [plan, setPlan] = useState({ driverId: load.driverId || '', vehicleId: load.vehicleId || '', plannedDateTime: load.plannedDateTime || '' })
  const company = companies.find(c => c.id === load.companyId)
  const address = addresses.find(a => a.id === load.addressId)
  const driver = drivers.find(d => d.id === load.driverId)
  const vehicle = vehicles.find(v => v.id === load.vehicleId)
  const isIcNakliye = load.shipmentType === 'ic_nakliye'

  const isYS = hasRole(user, ROLE.YS)
  const isAP = hasRole(user, ROLE.AP)
  const isDP = hasRole(user, ROLE.DP)

  const savePlan = async () => {
    try {
      await api(`loads/${load.id}/plan`, { method: 'POST', body: JSON.stringify(plan) })
      toast.success('Planlama kaydedildi')
      setPlanOpen(false)
      onRefresh()
    } catch (e) { toast.error(e.message) }
  }

  const changeStatus = async (status, note = '') => {
    try {
      await api(`loads/${load.id}/status`, { method: 'POST', body: JSON.stringify({ status, note }) })
      toast.success('Durum güncellendi: ' + STATUS_LABELS[status])
      onRefresh()
    } catch (e) { toast.error(e.message) }
  }

  const deleteLoad = async () => {
    if (!confirm('Bu yük silinsin mi?')) return
    try {
      await api(`loads/${load.id}`, { method: 'DELETE' })
      toast.success('Yük silindi')
      onBack()
      onRefresh()
    } catch (e) { toast.error(e.message) }
  }

  const buildWhatsAppMessage = () => {
    const lines = [
      `Merhaba${driver ? ' ' + driver.name : ''},`,
      '',
      `Yük Bilgisi:`,
      `Müşteri Firma: ${company?.name || '-'}`,
      `Yükleme Adresi: ${address?.name || ''} - ${address?.address || ''}, ${address?.district || ''}/${address?.city || ''}`,
      load.phone && `Telefon: ${load.phone}`,
      address?.contact && `Yetkili: ${address.contact}`,
      load.packages && `Kap: ${load.packages}`,
      load.kg && `Kg: ${load.kg}`,
      load.m3 && `m³: ${load.m3}`,
      load.dimensions && `Ölçüler: ${load.dimensions}`,
      (load.destCity || load.destCountry) && `Gidiş: ${load.destCity} ${load.destCountry}`.trim(),
      load.plannedDateTime && `Planlanan Tarih/Saat: ${load.plannedDateTime.replace('T', ' ')}`,
      vehicle && `Araç: ${vehicle.type} ${vehicle.plate}`,
      load.note && `Not: ${load.note}`,
    ].filter(Boolean)
    return lines.join('\n')
  }

  const sendWhatsApp = () => {
    if (!driver?.phone) return toast.error('Şoför telefonu tanımlı değil')
    const clean = driver.phone.replace(/[^0-9]/g, '')
    const text = encodeURIComponent(buildWhatsAppMessage())
    window.open(`https://wa.me/${clean}?text=${text}`, '_blank')
  }

  const nextActions = () => {
    const acts = []
    // yuk_sorumlusu can trigger creation/shipping/planning starts
    if (isYS && load.status === 'created' && !isIcNakliye) acts.push({ k: 'shipped', l: 'Gönderildi Olarak İşaretle', variant: 'default', I: PackageCheck })
    if (isYS && load.status === 'created' && isIcNakliye) acts.push({ k: 'planning', l: 'Planlamaya Al', variant: 'default', I: Clock })
    // arac_planlama can mark as in transit
    if (isAP && load.status === 'planned') acts.push({ k: 'in_transit', l: 'Yolda Olarak İşaretle', variant: 'default', I: Truck })
    // depocu (or yuk_sorumlusu) can mark as delivered
    if ((isDP || isYS) && (load.status === 'in_transit' || load.status === 'planned')) acts.push({ k: 'delivered', l: 'Depoya Ulaştı', variant: 'default', I: PackageCheck })
    return acts
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onBack} className="gap-1"><ArrowLeft className="w-4 h-4" />Listeye Dön</Button>
        <Badge className={STATUS_COLORS[load.status]}>{STATUS_LABELS[load.status]}</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main info */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl">{company?.name || 'Firma'}</CardTitle>
                  <CardDescription>{load.loadDate} · {SHIPMENT_TYPES[load.shipmentType]}</CardDescription>
                </div>
                {isYS && (
                  <Button variant="ghost" size="sm" onClick={deleteLoad} className="text-rose-600 hover:text-rose-700">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
              <Info label="Yükleme Adresi" value={address?.name || '-'} sub={address?.address} />
              <Info label="Yükleme Şehri" value={`${address?.district || ''} ${address?.city || ''}`.trim() || '-'} />
              <Info label="Telefon" value={load.phone || '-'} />
              <Info label="Kap" value={load.packages || '-'} />
              <Info label="Kg" value={load.kg || '-'} />
              <Info label="m³" value={load.m3 || '-'} />
              <Info label="Ölçüler" value={load.dimensions || '-'} />
              <Info label="Gidiş Şehir" value={load.destCity || '-'} />
              <Info label="Gidiş Ülke" value={load.destCountry || '-'} />
              {load.note && <div className="col-span-full"><Info label="Not" value={load.note} /></div>}
            </CardContent>
          </Card>

          {isIcNakliye && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Araç & Şoför Planlaması</CardTitle>
                    <CardDescription>İç nakliye için planlama bilgileri</CardDescription>
                  </div>
                  <Dialog open={planOpen} onOpenChange={setPlanOpen}>
                    {isAP && (
                      <DialogTrigger asChild>
                        <Button size="sm" className="gap-1">
                          {driver ? <><Edit className="w-4 h-4" />Düzenle</> : <><Plus className="w-4 h-4" />Planla</>}
                        </Button>
                      </DialogTrigger>
                    )}
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Şoför ve Araç Planla</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-3">
                        <div>
                          <Label>Şoför</Label>
                          <Select value={plan.driverId} onValueChange={v => setPlan({ ...plan, driverId: v })}>
                            <SelectTrigger><SelectValue placeholder="Şoför seçin" /></SelectTrigger>
                            <SelectContent>
                              {drivers.filter(d => d.active).map(d => <SelectItem key={d.id} value={d.id}>{d.name} · {d.phone}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Araç</Label>
                          <Select value={plan.vehicleId} onValueChange={v => setPlan({ ...plan, vehicleId: v })}>
                            <SelectTrigger><SelectValue placeholder="Araç seçin" /></SelectTrigger>
                            <SelectContent>
                              {vehicles.filter(v => v.active).map(v => <SelectItem key={v.id} value={v.id}>{v.type} · {v.plate}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Planlanan Tarih/Saat</Label>
                          <Input type="datetime-local" value={plan.plannedDateTime} onChange={e => setPlan({ ...plan, plannedDateTime: e.target.value })} />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setPlanOpen(false)}>İptal</Button>
                        <Button onClick={savePlan}>Planla</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                <Info label="Şoför" value={driver ? driver.name : 'Atanmadı'} sub={driver?.phone} />
                <Info label="Araç" value={vehicle ? `${vehicle.type} · ${vehicle.plate}` : 'Atanmadı'} />
                <Info label="Planlanan" value={load.plannedDateTime ? load.plannedDateTime.replace('T', ' ') : '-'} />
              </CardContent>
              {driver && isAP && (
                <div className="px-6 pb-6">
                  <Button onClick={sendWhatsApp} className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700" size="lg">
                    <MessageCircle className="w-5 h-5" />
                    WhatsApp ile Şoföre Gönder
                  </Button>
                  <p className="text-xs text-slate-500 mt-2 text-center">Yük bilgileri WhatsApp'ta hazır mesaj olarak açılır.</p>
                </div>
              )}
            </Card>
          )}

          {/* Actions */}
          {nextActions().length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-base">Durum İşlemleri</CardTitle></CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {nextActions().map(a => (
                  <Button key={a.k} onClick={() => changeStatus(a.k)} variant={a.variant} className="gap-2">
                    <a.I className="w-4 h-4" />{a.l}
                  </Button>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Timeline */}
        <Card>
          <CardHeader><CardTitle className="text-base">Durum Geçmişi</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(load.statusHistory || []).slice().reverse().map((h, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${i === 0 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    {i !== load.statusHistory.length - 1 && <div className="w-px flex-1 bg-slate-200 min-h-4" />}
                  </div>
                  <div className="pb-2">
                    <p className="font-medium text-sm">{STATUS_LABELS[h.status]}</p>
                    <p className="text-xs text-slate-500">{new Date(h.at).toLocaleString('tr-TR')}</p>
                    {h.note && <p className="text-xs text-slate-600 mt-1">{h.note}</p>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Info({ label, value, sub }) {
  return (
    <div>
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className="font-medium">{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  )
}

// ============ COMPANIES VIEW ============
function CompaniesView({ companies, addresses, onRefresh }) {
  const [openCompany, setOpenCompany] = useState(false)
  const [editCompany, setEditCompany] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [openAddr, setOpenAddr] = useState(null) // companyId or null
  const [editAddr, setEditAddr] = useState(null)

  const del = async (id) => {
    if (!confirm('Firma ve tüm adresleri silinecek. Emin misiniz?')) return
    try { await api(`companies/${id}`, { method: 'DELETE' }); toast.success('Silindi'); onRefresh() } catch (e) { toast.error(e.message) }
  }
  const delAddr = async (id) => {
    if (!confirm('Adres silinsin mi?')) return
    try { await api(`addresses/${id}`, { method: 'DELETE' }); toast.success('Silindi'); onRefresh() } catch (e) { toast.error(e.message) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Firmalar</h2>
          <p className="text-slate-500 text-sm">{companies.length} firma tanımlı</p>
        </div>
        <Dialog open={openCompany} onOpenChange={setOpenCompany}>
          <DialogTrigger asChild><Button className="gap-2"><Plus className="w-4 h-4" />Yeni Firma</Button></DialogTrigger>
          <CompanyForm onClose={() => setOpenCompany(false)} onSaved={() => { setOpenCompany(false); onRefresh() }} />
        </Dialog>
      </div>

      <div className="space-y-2">
        {companies.map(c => {
          const addrs = addresses.filter(a => a.companyId === c.id)
          const isOpen = expanded === c.id
          return (
            <Card key={c.id}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-slate-500" />
                      <span className="font-semibold">{c.name}</span>
                      {!c.active && <Badge variant="outline">Pasif</Badge>}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{c.phone} · {c.email} · {addrs.length} adres</p>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="outline" size="sm" onClick={() => setExpanded(isOpen ? null : c.id)}>{isOpen ? 'Kapat' : 'Adresler'}</Button>
                    <Button variant="outline" size="sm" onClick={() => setEditCompany(c)}><Edit className="w-3.5 h-3.5" /></Button>
                    <Button variant="outline" size="sm" onClick={() => del(c.id)} className="text-rose-600"><Trash2 className="w-3.5 h-3.5" /></Button>
                  </div>
                </div>
                {isOpen && (
                  <div className="mt-3 border-t pt-3">
                    <div className="flex justify-between items-center mb-2">
                      <p className="text-sm font-medium">Adresler</p>
                      <Button size="sm" variant="outline" onClick={() => setOpenAddr(c.id)}><Plus className="w-3.5 h-3.5 mr-1" />Adres Ekle</Button>
                    </div>
                    {addrs.length === 0 ? (
                      <p className="text-sm text-slate-500">Henüz adres yok</p>
                    ) : (
                      <div className="space-y-2">
                        {addrs.map(a => (
                          <div key={a.id} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                            <div className="min-w-0">
                              <p className="text-sm font-medium">{a.name} <span className="text-slate-400 font-normal">· {a.district}/{a.city}</span></p>
                              <p className="text-xs text-slate-500 truncate">{a.address} {a.contact && `· ${a.contact}`} {a.phone && `· ${a.phone}`}</p>
                            </div>
                            <div className="flex gap-1 flex-shrink-0">
                              <Button variant="ghost" size="sm" onClick={() => setEditAddr(a)}><Edit className="w-3.5 h-3.5" /></Button>
                              <Button variant="ghost" size="sm" onClick={() => delAddr(a.id)} className="text-rose-600"><Trash2 className="w-3.5 h-3.5" /></Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {editCompany && (
        <Dialog open={!!editCompany} onOpenChange={() => setEditCompany(null)}>
          <CompanyForm company={editCompany} onClose={() => setEditCompany(null)} onSaved={() => { setEditCompany(null); onRefresh() }} />
        </Dialog>
      )}
      {openAddr && (
        <Dialog open={!!openAddr} onOpenChange={() => setOpenAddr(null)}>
          <AddressForm companyId={openAddr} onClose={() => setOpenAddr(null)} onSaved={() => { setOpenAddr(null); onRefresh() }} />
        </Dialog>
      )}
      {editAddr && (
        <Dialog open={!!editAddr} onOpenChange={() => setEditAddr(null)}>
          <AddressForm address={editAddr} companyId={editAddr.companyId} onClose={() => setEditAddr(null)} onSaved={() => { setEditAddr(null); onRefresh() }} />
        </Dialog>
      )}
    </div>
  )
}

function CompanyForm({ company, onClose, onSaved }) {
  const [f, setF] = useState({
    name: company?.name || '', phone: company?.phone || '', email: company?.email || '', active: company?.active !== false,
  })
  const save = async () => {
    if (!f.name) return toast.error('Firma adı zorunlu')
    try {
      if (company) await api(`companies/${company.id}`, { method: 'PUT', body: JSON.stringify(f) })
      else await api('companies', { method: 'POST', body: JSON.stringify(f) })
      toast.success('Kaydedildi')
      onSaved()
    } catch (e) { toast.error(e.message) }
  }
  return (
    <DialogContent>
      <DialogHeader><DialogTitle>{company ? 'Firma Düzenle' : 'Yeni Firma'}</DialogTitle></DialogHeader>
      <div className="space-y-3">
        <div><Label>Firma Adı *</Label><Input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} /></div>
        <div><Label>Telefon</Label><Input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} /></div>
        <div><Label>E-posta</Label><Input value={f.email} onChange={e => setF({ ...f, email: e.target.value })} /></div>
        <div className="flex items-center gap-2"><Switch checked={f.active} onCheckedChange={v => setF({ ...f, active: v })} /><Label>Aktif</Label></div>
      </div>
      <DialogFooter><Button variant="outline" onClick={onClose}>İptal</Button><Button onClick={save}>Kaydet</Button></DialogFooter>
    </DialogContent>
  )
}

function AddressForm({ address, companyId, onClose, onSaved }) {
  const [f, setF] = useState({
    name: address?.name || '', address: address?.address || '', city: address?.city || '',
    district: address?.district || '', phone: address?.phone || '', contact: address?.contact || '',
    coordinate: address?.coordinate || '',
  })
  const save = async () => {
    if (!f.name) return toast.error('Adres adı zorunlu')
    try {
      if (address) await api(`addresses/${address.id}`, { method: 'PUT', body: JSON.stringify(f) })
      else await api('addresses', { method: 'POST', body: JSON.stringify({ ...f, companyId }) })
      toast.success('Kaydedildi')
      onSaved()
    } catch (e) { toast.error(e.message) }
  }
  return (
    <DialogContent>
      <DialogHeader><DialogTitle>{address ? 'Adres Düzenle' : 'Yeni Adres'}</DialogTitle></DialogHeader>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2"><Label>Adres Adı *</Label><Input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} placeholder="örn. Merkez Fabrika" /></div>
        <div className="col-span-2"><Label>Açık Adres</Label><Textarea rows={2} value={f.address} onChange={e => setF({ ...f, address: e.target.value })} /></div>
        <div><Label>İl</Label><Input value={f.city} onChange={e => setF({ ...f, city: e.target.value })} /></div>
        <div><Label>İlçe</Label><Input value={f.district} onChange={e => setF({ ...f, district: e.target.value })} /></div>
        <div><Label>Telefon</Label><Input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} /></div>
        <div><Label>Yetkili</Label><Input value={f.contact} onChange={e => setF({ ...f, contact: e.target.value })} /></div>
        <div className="col-span-2"><Label>Koordinat</Label><Input value={f.coordinate} onChange={e => setF({ ...f, coordinate: e.target.value })} placeholder="41.0082,28.9784" /></div>
      </div>
      <DialogFooter><Button variant="outline" onClick={onClose}>İptal</Button><Button onClick={save}>Kaydet</Button></DialogFooter>
    </DialogContent>
  )
}

// ============ DRIVERS VIEW ============
function DriversView({ drivers, onRefresh }) {
  const [open, setOpen] = useState(false)
  const [edit, setEdit] = useState(null)
  const del = async (id) => {
    if (!confirm('Şoför silinsin mi?')) return
    try { await api(`drivers/${id}`, { method: 'DELETE' }); toast.success('Silindi'); onRefresh() } catch (e) { toast.error(e.message) }
  }
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold">Şoförler</h2><p className="text-slate-500 text-sm">{drivers.length} şoför</p></div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button className="gap-2"><Plus className="w-4 h-4" />Yeni Şoför</Button></DialogTrigger>
          <DriverForm onClose={() => setOpen(false)} onSaved={() => { setOpen(false); onRefresh() }} />
        </Dialog>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {drivers.map(d => (
          <Card key={d.id}>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center flex-shrink-0"><User className="w-5 h-5" /></div>
                  <div className="min-w-0">
                    <p className="font-medium truncate">{d.name}</p>
                    <p className="text-xs text-slate-500">{d.phone}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  {!d.active && <Badge variant="outline" className="mr-1">Pasif</Badge>}
                  <Button variant="ghost" size="sm" onClick={() => setEdit(d)}><Edit className="w-3.5 h-3.5" /></Button>
                  <Button variant="ghost" size="sm" onClick={() => del(d.id)} className="text-rose-600"><Trash2 className="w-3.5 h-3.5" /></Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {edit && <Dialog open={!!edit} onOpenChange={() => setEdit(null)}><DriverForm driver={edit} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); onRefresh() }} /></Dialog>}
    </div>
  )
}

function DriverForm({ driver, onClose, onSaved }) {
  const [f, setF] = useState({ name: driver?.name || '', phone: driver?.phone || '', active: driver?.active !== false })
  const save = async () => {
    if (!f.name) return toast.error('Ad soyad zorunlu')
    try {
      if (driver) await api(`drivers/${driver.id}`, { method: 'PUT', body: JSON.stringify(f) })
      else await api('drivers', { method: 'POST', body: JSON.stringify(f) })
      toast.success('Kaydedildi'); onSaved()
    } catch (e) { toast.error(e.message) }
  }
  return (
    <DialogContent>
      <DialogHeader><DialogTitle>{driver ? 'Şoför Düzenle' : 'Yeni Şoför'}</DialogTitle></DialogHeader>
      <div className="space-y-3">
        <div><Label>Ad Soyad *</Label><Input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} /></div>
        <div><Label>Telefon (WhatsApp için)</Label><Input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} placeholder="905xx... veya 05xx..." /></div>
        <div className="flex items-center gap-2"><Switch checked={f.active} onCheckedChange={v => setF({ ...f, active: v })} /><Label>Aktif</Label></div>
      </div>
      <DialogFooter><Button variant="outline" onClick={onClose}>İptal</Button><Button onClick={save}>Kaydet</Button></DialogFooter>
    </DialogContent>
  )
}

// ============ VEHICLES VIEW ============
function VehiclesView({ vehicles, onRefresh }) {
  const [open, setOpen] = useState(false)
  const [edit, setEdit] = useState(null)
  const del = async (id) => {
    if (!confirm('Araç silinsin mi?')) return
    try { await api(`vehicles/${id}`, { method: 'DELETE' }); toast.success('Silindi'); onRefresh() } catch (e) { toast.error(e.message) }
  }
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold">Araçlar</h2><p className="text-slate-500 text-sm">{vehicles.length} araç</p></div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button className="gap-2"><Plus className="w-4 h-4" />Yeni Araç</Button></DialogTrigger>
          <VehicleForm onClose={() => setOpen(false)} onSaved={() => { setOpen(false); onRefresh() }} />
        </Dialog>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {vehicles.map(v => (
          <Card key={v.id}>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-indigo-100 text-indigo-700 rounded-lg flex items-center justify-center flex-shrink-0"><Truck className="w-5 h-5" /></div>
                  <div className="min-w-0">
                    <p className="font-medium">{v.plate}</p>
                    <p className="text-xs text-slate-500">{v.type}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  {!v.active && <Badge variant="outline">Pasif</Badge>}
                  <Button variant="ghost" size="sm" onClick={() => setEdit(v)}><Edit className="w-3.5 h-3.5" /></Button>
                  <Button variant="ghost" size="sm" onClick={() => del(v.id)} className="text-rose-600"><Trash2 className="w-3.5 h-3.5" /></Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {edit && <Dialog open={!!edit} onOpenChange={() => setEdit(null)}><VehicleForm vehicle={edit} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); onRefresh() }} /></Dialog>}
    </div>
  )
}

function VehicleForm({ vehicle, onClose, onSaved }) {
  const [f, setF] = useState({ type: vehicle?.type || '', plate: vehicle?.plate || '', active: vehicle?.active !== false })
  const save = async () => {
    if (!f.plate) return toast.error('Plaka zorunlu')
    try {
      if (vehicle) await api(`vehicles/${vehicle.id}`, { method: 'PUT', body: JSON.stringify(f) })
      else await api('vehicles', { method: 'POST', body: JSON.stringify(f) })
      toast.success('Kaydedildi'); onSaved()
    } catch (e) { toast.error(e.message) }
  }
  return (
    <DialogContent>
      <DialogHeader><DialogTitle>{vehicle ? 'Araç Düzenle' : 'Yeni Araç'}</DialogTitle></DialogHeader>
      <div className="space-y-3">
        <div><Label>Araç Tipi</Label><Input value={f.type} onChange={e => setF({ ...f, type: e.target.value })} placeholder="örn. Kamyonet, Tır" /></div>
        <div><Label>Plaka *</Label><Input value={f.plate} onChange={e => setF({ ...f, plate: e.target.value })} placeholder="34 ABC 123" /></div>
        <div className="flex items-center gap-2"><Switch checked={f.active} onCheckedChange={v => setF({ ...f, active: v })} /><Label>Aktif</Label></div>
      </div>
      <DialogFooter><Button variant="outline" onClick={onClose}>İptal</Button><Button onClick={save}>Kaydet</Button></DialogFooter>
    </DialogContent>
  )
}

export default App
