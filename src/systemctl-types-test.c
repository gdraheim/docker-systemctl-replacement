#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <regex.h>
#include <stdio.h>
#include "systemctl-logging.h"
#include "systemctl-types.h"
#include "systemctl-shlex.h"
#include <assert.h>


void test_001()
{
    str_t s = NULL;
    s = str_dup("foo");
    printf("dup: '%s'\n", s);
    assert(! strcmp(s, "foo"));
    str_free(s);
}
  
void test_002()
{
    str_t s = str_dup2("foo", "bar");
    printf("dup2: '%s'\n", s);
    assert(! strcmp(s, "foobar"));
    str_free(s);
}

void test_003()
{
    str_t s = str_lstrip(" foo ");
    printf("lstrip: '%s'\n", s);
    assert(! strcmp(s, "foo "));
    str_free(s);
}

void test_004()
{
    str_t s = str_rstrip(" foo ");
    printf("rstrip: '%s'\n", s);
    assert(! strcmp(s, " foo"));
    str_free(s);
}
  
void test_005()
{
    str_t s = str_strip(" foo ");
    printf("strip: '%s'\n", s);
    assert(! strcmp(s, "foo"));
    str_free(s);
}
  
  /* ............ */
void test_011()
{
    str_list_t g = str_list_NULL;
    str_list_add(&g, "foo");
    str_list_add(&g, "bar");
    str_t s = str_list_join(&g, ".");
    printf("add/join: '%s'\n", s);
    assert(! strcmp(s, "foo.bar"));
    str_list_null(&g);
    str_free(s);
}

void test_012()
{
    str_list_t* g = str_list_new();
    str_list_add(g, "foo");
    str_list_add(g, "bar");
    str_list_adds(g, str_cut("foo", 1, 3));
    str_t s = str_list_join(g, ".");
    printf("add/join: '%s'\n", s);
    assert(! strcmp(s, "foo.bar.oo"));
    str_list_free(g);
    str_free(s);
}

void test_021()
{
    str_dict_t g = str_dict_NULL;
    str_dict_add(&g, "foo", "zen");
    str_dict_add(&g, "bar", "coo");
    str_list_t* keys = str_dict_keys(&g);
    str_t s = str_list_join(keys, ".");
    logg_info("dict add/keys: '%s'", s);
    assert(! strcmp(s, "bar.foo"));
    str_list_free(keys);
    str_dict_null(&g);
    str_free(s);
}

void test_022()
{
    str_dict_t g = str_dict_NULL;
    str_dict_add(&g, "foo", "zen");
    str_dict_add(&g, "bar", "coo");
    str_dict_add(&g, "coo", "foo");
    str_dict_add(&g, "zen", "bar");
    str_dict_add(&g, "all", "oki");
    str_list_t* keys = str_dict_keys(&g);
    str_t s = str_list_join(keys, ".");
    logg_info("dict add/keys: '%s'", s);
    assert(! strcmp(s, "all.bar.coo.foo.zen"));
    str_list_free(keys);
    str_dict_null(&g);
    str_free(s);
}

void test_101()
{
    str_list_dict_t* h = str_list_dict_new();
    str_list_t* t = str_list_new();
    str_list_add(t, "foo");
    str_list_add(t, "bar");
    str_list_dict_add(h, "zoo", t);
    str_t s = str_list_dict_to_json(h);
    logg_info("listdict add/join: %s", s);
    assert(! strcmp(s, "{\"zoo\": [\"foo\", \"bar\"]}"));
    str_list_dict_free(h);
    str_list_free(t);
    str_free(s);
}

void test_102()
{
    str_list_dict_dict_t* g = str_list_dict_dict_new();
    str_list_dict_t* h = str_list_dict_new();
    str_list_t* t = str_list_new();
    str_list_add(t, "foo");
    str_list_add(t, "bar");
    str_list_dict_add(h, "zoo", t);
    str_list_dict_dict_add(g, "foo", h);
    str_t s = str_list_dict_dict_to_json(g);
    logg_info("listdictdict add/join: %s", s);
    assert(! strcmp(s, "{\"foo\": {\"zoo\": [\"foo\", \"bar\"]}}"));
    str_list_dict_dict_free(g);
    str_list_dict_free(h);
    str_list_free(t);
    str_free(s);
}

void test_400()
{
    str_list_t* res = shlex_split("a b 'c d' \"e f\"");
    str_t s = str_list_to_json(res);
    logg_info("shlex.split: %s", s);
    assert(! strcmp(s, "[\"a\", \"b\", \"c d\", \"e f\"]"));
    str_list_free(res);
    str_free(s);
}

void test_401()
{
    str_list_t* res = shlex_parse("a b 'c d' \"e f\"");
    str_t s = str_list_to_json(res);
    logg_info("shlex.parse: %s", s);
    assert(! strcmp(s, "[\"a\", \"b\", \"'c d'\", \"\\\"e f\\\"\"]"));
    str_list_free(res);
    str_free(s);
}
  
int
main(int argc, char** argv)
{
    logg_setlevel(LOG_INFO);
    test_001();
    test_002();
    test_003();
    test_004();
    test_005();
    test_011();
    test_012();
    test_021();
    test_022();
    test_101();
    test_102();
    test_400();
    test_401();
    return 0;
}
