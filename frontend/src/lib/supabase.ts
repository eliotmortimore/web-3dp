import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://oeqhnussmevwlesbnbmp.supabase.co';
const supabaseKey = 'sb_publishable_sNye7Q2LTq6MB011zOOM8A_GxLEJhBi';

export const supabase = createClient(supabaseUrl, supabaseKey);
