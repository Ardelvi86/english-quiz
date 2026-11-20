-- Create a public bucket first, then replace both placeholders below.
-- Public buckets allow anonymous reads; these policies restrict mutations
-- to the Firebase admin that owns the shared-content/<uid>/ folder.

create policy "Firebase admins can read shared exercise images"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'exercise-images'
  and (storage.foldername(name))[1] = 'shared-content'
  and (storage.foldername(name))[2] = (select auth.jwt() ->> 'sub')
  and (select auth.jwt() ->> 'admin') = 'true'
  and (select auth.jwt() ->> 'iss') =
      'https://securetoken.google.com/english-quiz-app-3f3b3'
  and (select auth.jwt() ->> 'aud') = 'english-quiz-app-3f3b3'
);

create policy "Firebase admins can upload shared exercise images"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'exercise-images'
  and (storage.foldername(name))[1] = 'shared-content'
  and (storage.foldername(name))[2] = (select auth.jwt() ->> 'sub')
  and (select auth.jwt() ->> 'admin') = 'true'
  and (select auth.jwt() ->> 'iss') =
      'https://securetoken.google.com/english-quiz-app-3f3b3'
  and (select auth.jwt() ->> 'aud') = 'english-quiz-app-3f3b3'
);

create policy "Firebase admins can update shared exercise images"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'exercise-images'
  and (storage.foldername(name))[1] = 'shared-content'
  and (storage.foldername(name))[2] = (select auth.jwt() ->> 'sub')
  and (select auth.jwt() ->> 'admin') = 'true'
  and (select auth.jwt() ->> 'iss') =
      'https://securetoken.google.com/english-quiz-app-3f3b3'
  and (select auth.jwt() ->> 'aud') = 'english-quiz-app-3f3b3'
)
with check (
  bucket_id = 'exercise-images'
  and (storage.foldername(name))[1] = 'shared-content'
  and (storage.foldername(name))[2] = (select auth.jwt() ->> 'sub')
  and (select auth.jwt() ->> 'admin') = 'true'
  and (select auth.jwt() ->> 'iss') =
      'https://securetoken.google.com/english-quiz-app-3f3b3'
  and (select auth.jwt() ->> 'aud') = 'english-quiz-app-3f3b3'
);

create policy "Firebase admins can delete shared exercise images"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'exercise-images'
  and (storage.foldername(name))[1] = 'shared-content'
  and (storage.foldername(name))[2] = (select auth.jwt() ->> 'sub')
  and (select auth.jwt() ->> 'admin') = 'true'
  and (select auth.jwt() ->> 'iss') =
      'https://securetoken.google.com/english-quiz-app-3f3b3'
  and (select auth.jwt() ->> 'aud') = 'english-quiz-app-3f3b3'
);
