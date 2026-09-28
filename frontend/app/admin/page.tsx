import AdminDesktop from '@/components/AdminDesktop';
import AdminUnavailable from '@/components/AdminUnavailable';
import { standalone } from '@/lib/mode';
export default function AdminPage(){return standalone ? <AdminUnavailable/> : <AdminDesktop/>;}
