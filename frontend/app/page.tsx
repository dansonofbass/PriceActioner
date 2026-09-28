import FullWorkspace from '@/components/FullWorkspace';
import StandaloneWorkspace from '@/components/StandaloneWorkspace';
import { standalone } from '@/lib/mode';
export default function Home(){return standalone ? <StandaloneWorkspace/> : <FullWorkspace/>;}
